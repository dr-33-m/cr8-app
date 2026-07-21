"""
RustFS object storage for user .blend files.

RustFS ships no SDK of its own — it is S3-compatible, so this is boto3 pointed at
the RustFS endpoint with s3v4 signatures and path-style addressing.

Two clients, not one. Presigned URLs sign the Host header, so a URL signed for the
public endpoint fails with SignatureDoesNotMatch when sent to the internal one (and
vice versa). Pick the client by where the URL is going:

    browser  -> public   (through the Cloudflare tunnel, 100MB request body cap)
    instance -> internal (over the VPN, no cap)

That cap is why uploads from the browser are multipart: a 1GB single PUT would 413.
Instances bypass the tunnel entirely, so their saves stay a single PUT.

Layout: s3://{bucket}/users/{user_id}/{filename}.blend  — user_id is the internal
DB UUID, never the socket-layer `username` (which is a fallback-chained display
name that two users can collide on).
"""

import logging
import re
import unicodedata
from typing import Any
from urllib.parse import quote

import boto3
from botocore.client import Config

from .config import DeploymentConfig

logger = logging.getLogger(__name__)

# Single PUT below this, multipart above. Deliberately set rather than inherited:
# Uppy's default is 100 MiB (104.8 MB), which overshoots Cloudflare's 100 MB cap —
# files in that band would take the single-PUT path and 413. Keep in sync with
# SINGLE_PUT_MAX_BYTES in the frontend uploader.
SINGLE_PUT_MAX_BYTES = 50 * 1024 * 1024

# Hard ceiling on a stored blend file.
MAX_BLEND_BYTES = 2 * 1024 * 1024 * 1024

# S3 requires every part except the last to be >= 5MB, so capping the part number
# bounds a well-behaved multipart upload at roughly MAX_BLEND_BYTES.
#
# This is a bound, not a guarantee: a hostile client can send oversized parts, and
# nothing here signs each part's length. Real enforcement needs a per-user quota
# (see the plan's Known gaps). The gate that matters today is that storage is
# invite-gated to approved users.
S3_MIN_PART_BYTES = 5 * 1024 * 1024
MAX_PART_NUMBER = MAX_BLEND_BYTES // S3_MIN_PART_BYTES

PRESIGN_TTL_SECONDS = 3600

_public_client = None
_internal_client = None


class StorageError(Exception):
    """Storage misuse that should surface as a 4xx, not a 500."""


def _build_client(endpoint: str):
    config = DeploymentConfig.get()
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=config.RUSTFS_ACCESS_KEY,
        aws_secret_access_key=config.RUSTFS_SECRET_KEY,
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )


def public_client():
    """Client for URLs the browser will use. Signs against the tunnelled hostname."""
    global _public_client
    if _public_client is None:
        _public_client = _build_client(DeploymentConfig.get().RUSTFS_PUBLIC_ENDPOINT)
    return _public_client


def internal_client():
    """Client for URLs a VastAI instance will use. Signs against the VPN hostname."""
    global _internal_client
    if _internal_client is None:
        _internal_client = _build_client(DeploymentConfig.get().RUSTFS_INTERNAL_ENDPOINT)
    return _internal_client


def reset_clients():
    """Drop cached clients (tests, or after a config change)."""
    global _public_client, _internal_client
    _public_client = None
    _internal_client = None


def _bucket() -> str:
    return DeploymentConfig.get().RUSTFS_BUCKET


def user_prefix(user_id: str) -> str:
    return f"users/{user_id}/"


def sanitize_filename(filename: str) -> str:
    """
    Reduce a client-supplied filename to a bare, safe .blend leaf name.

    The client controls this string, so it is treated as hostile: strip any path
    structure, allow a conservative character set, and require the .blend suffix.
    """
    leaf = filename.replace("\\", "/").split("/")[-1].strip()
    if not leaf or leaf in (".", ".."):
        raise StorageError("Invalid filename")
    if not leaf.lower().endswith(".blend"):
        raise StorageError("Only .blend files are supported")
    if not re.fullmatch(r"[A-Za-z0-9 ._-]{1,200}", leaf):
        raise StorageError(
            "Filename may only contain letters, numbers, spaces, dots, underscores and hyphens"
        )
    return leaf


def build_key(user_id: str, filename: str) -> str:
    return user_prefix(user_id) + sanitize_filename(filename)


def assert_owned(key: str, user_id: str) -> str:
    """
    The single ownership gate. Every path that accepts a client-supplied key calls
    this — including all four multipart endpoints, where signing a part for someone
    else's key would otherwise let a caller write into their prefix.
    """
    if ".." in key or key != key.strip():
        raise StorageError("Invalid key")
    if not key.startswith(user_prefix(user_id)):
        raise StorageError("Key does not belong to the current user")
    return key


def assert_size(size: int):
    if size <= 0:
        raise StorageError("Size must be greater than zero")
    if size > MAX_BLEND_BYTES:
        raise StorageError(
            f"File is larger than the {MAX_BLEND_BYTES // (1024 * 1024 * 1024)}GB limit"
        )


def list_blend_files(user_id: str) -> list[dict[str, Any]]:
    """List the user's stored blend files. S3 is the source of truth — there is no
    mirror table, so this listing is the whole inventory."""
    client = public_client()
    paginator = client.get_paginator("list_objects_v2")
    files: list[dict[str, Any]] = []
    for page in paginator.paginate(Bucket=_bucket(), Prefix=user_prefix(user_id)):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(".blend"):
                continue
            files.append(
                {
                    "key": key,
                    "filename": key.rsplit("/", 1)[-1],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                }
            )
    files.sort(key=lambda f: f["last_modified"], reverse=True)
    return files


def delete_blend_file(key: str, user_id: str):
    assert_owned(key, user_id)
    public_client().delete_object(Bucket=_bucket(), Key=key)
    logger.info(f"Deleted {key}")


# --- Upload: single PUT (small files) ---

def presign_upload(user_id: str, filename: str, size: int) -> dict[str, str]:
    """
    Presign a single-PUT upload for the browser.

    ContentLength is signed, so the browser cannot upload more than it declared —
    the size limit is enforced by the signature rather than by trusting the client.
    """
    assert_size(size)
    if size > SINGLE_PUT_MAX_BYTES:
        raise StorageError("File requires a multipart upload")
    key = build_key(user_id, filename)
    url = public_client().generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": _bucket(), "Key": key, "ContentLength": size},
        ExpiresIn=PRESIGN_TTL_SECONDS,
    )
    return {"upload_url": url, "key": key}


# --- Upload: multipart (large files) ---
# Mandatory for anything over the tunnel's 100MB request body cap, and the reason
# a 1GB upload is possible at all. Maps 1:1 onto Uppy's aws-s3 callbacks.

def create_multipart_upload(user_id: str, filename: str) -> dict[str, str]:
    key = build_key(user_id, filename)
    response = public_client().create_multipart_upload(
        Bucket=_bucket(),
        Key=key,
        ContentType="application/octet-stream",
    )
    logger.info(f"Started multipart upload {response['UploadId']} for {key}")
    return {"uploadId": response["UploadId"], "key": key}


def presign_part(key: str, upload_id: str, part_number: int, user_id: str) -> str:
    assert_owned(key, user_id)
    if part_number < 1 or part_number > MAX_PART_NUMBER:
        raise StorageError(f"Part number must be between 1 and {MAX_PART_NUMBER}")
    return public_client().generate_presigned_url(
        ClientMethod="upload_part",
        Params={
            "Bucket": _bucket(),
            "Key": key,
            "UploadId": upload_id,
            "PartNumber": part_number,
        },
        ExpiresIn=PRESIGN_TTL_SECONDS,
    )


def list_parts(key: str, upload_id: str, user_id: str) -> list[dict[str, Any]]:
    """
    Parts already uploaded for an in-progress multipart upload.

    This is what makes a resume possible: on retry Uppy asks which parts already
    landed and skips them, so a blip at 900MB of a 1GB upload costs one part
    rather than the whole transfer.
    """
    assert_owned(key, user_id)
    client = public_client()
    paginator = client.get_paginator("list_parts")
    parts: list[dict[str, Any]] = []
    for page in paginator.paginate(Bucket=_bucket(), Key=key, UploadId=upload_id):
        for part in page.get("Parts", []):
            parts.append(
                {
                    "PartNumber": part["PartNumber"],
                    "Size": part["Size"],
                    "ETag": part["ETag"],
                }
            )
    return parts


def complete_multipart_upload(
    key: str, upload_id: str, parts: list[dict[str, Any]], user_id: str
) -> dict[str, str]:
    assert_owned(key, user_id)
    ordered = sorted(parts, key=lambda p: p["PartNumber"])
    response = public_client().complete_multipart_upload(
        Bucket=_bucket(),
        Key=key,
        UploadId=upload_id,
        MultipartUpload={"Parts": ordered},
    )
    logger.info(f"Completed multipart upload {upload_id} for {key} ({len(ordered)} parts)")
    return {"location": response.get("Location", "")}


def abort_multipart_upload(key: str, upload_id: str, user_id: str):
    assert_owned(key, user_id)
    public_client().abort_multipart_upload(
        Bucket=_bucket(), Key=key, UploadId=upload_id
    )
    logger.info(f"Aborted multipart upload {upload_id} for {key}")


# --- Instance-bound URLs (Phase 2/3) ---
# Signed against the internal endpoint: these are handed to a VastAI instance, which
# reaches RustFS over the VPN. Signing these with the public client is the mistake
# this module's two-client split exists to prevent — it surfaces as an opaque
# SignatureDoesNotMatch at launch or save time.

def presign_download(key: str, ttl: int = PRESIGN_TTL_SECONDS) -> str:
    """Presign a GET for launch-blender.sh to curl the .blend onto the instance."""
    return internal_client().generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": _bucket(), "Key": key},
        ExpiresIn=ttl,
    )


# --- Renders ---
# Layout: users/{user_id}/renders/{project}/{kind}/{name}.{ext}
#
# `project` is derived server-side from the session's open blend key, never from
# the client. `kind` splits images from videos so animation output lands later
# without a migration or a re-listing scheme.
#
# Note both presign helpers below sign against the PUBLIC endpoint, including the
# one handed to a VastAI instance. That looks like it contradicts the "instance ->
# internal" rule at the top of this module, and it is deliberate: RustFS sits
# behind NAT with the Cloudflare tunnel as its only ingress, so an instance
# reaches it the same way a browser does. This matches the working multipart save
# path, which signs its part URLs with the public client too.

RENDER_KINDS = ("images", "videos")
THUMB_SUFFIX = ".thumb.jpg"
RENDER_IMAGE_EXT = ".png"

# A render is a single frame, not a project file — much smaller than a .blend.
# Kept well under MAX_BLEND_BYTES so a runaway output can't fill a bucket.
MAX_RENDER_BYTES = 512 * 1024 * 1024


def render_prefix(user_id: str, project: str = None, kind: str = None) -> str:
    prefix = f"{user_prefix(user_id)}renders/"
    if project:
        prefix += f"{project}/"
        if kind:
            prefix += f"{kind}/"
    return prefix


def sanitize_project_slug(project: str) -> str:
    """Validate a project folder name.

    Inputs reach this from two directions — derived from an already-sanitized
    blend filename, or supplied by the browser as a Library route param — so it
    is validated rather than trusted in either case.
    """
    slug = (project or "").strip()
    if not slug or slug in (".", ".."):
        raise StorageError("Invalid project name")
    if not re.fullmatch(r"[A-Za-z0-9 ._-]{1,200}", slug):
        raise StorageError("Invalid project name")
    return slug


def project_slug_from_blend_key(blend_key: str) -> str:
    """`users/{id}/Bedroom Scene.blend` -> `Bedroom Scene`."""
    leaf = (blend_key or "").rsplit("/", 1)[-1]
    if leaf.lower().endswith(".blend"):
        leaf = leaf[: -len(".blend")]
    return sanitize_project_slug(leaf)


def sanitize_render_name(name: str) -> str:
    """Reduce a render name to a safe, extensionless leaf.

    The extension is added by build_render_key rather than accepted from the
    caller, so a name can never smuggle in a different content type.
    """
    leaf = (name or "").replace("\\", "/").split("/")[-1].strip()
    if leaf.lower().endswith(RENDER_IMAGE_EXT):
        leaf = leaf[: -len(RENDER_IMAGE_EXT)]
    if not leaf or leaf in (".", ".."):
        raise StorageError("Invalid render name")
    if not re.fullmatch(r"[A-Za-z0-9 ._-]{1,200}", leaf):
        raise StorageError(
            "Render name may only contain letters, numbers, spaces, dots, "
            "underscores and hyphens"
        )
    return leaf


def build_render_key(user_id: str, project: str, name: str,
                     kind: str = "images") -> str:
    if kind not in RENDER_KINDS:
        raise StorageError(f"Unknown render kind '{kind}'")
    slug = sanitize_project_slug(project)
    leaf = sanitize_render_name(name)
    return f"{render_prefix(user_id, slug, kind)}{leaf}{RENDER_IMAGE_EXT}"


def thumb_key_for(key: str) -> str:
    """Thumbnail sibling of a render key. Derived, never stored separately, so
    the two can't drift apart."""
    base = key
    if base.lower().endswith(RENDER_IMAGE_EXT):
        base = base[: -len(RENDER_IMAGE_EXT)]
    return base + THUMB_SUFFIX


def is_thumb(key: str) -> bool:
    return key.lower().endswith(THUMB_SUFFIX)


def list_render_projects(user_id: str) -> list[dict[str, Any]]:
    """Render projects as folders, with per-kind counts and a cover thumbnail.

    One paginated listing over the whole renders/ prefix rather than a call per
    project: the object count here is small, and this keeps the Library's first
    paint to a single round trip.
    """
    client = public_client()
    paginator = client.get_paginator("list_objects_v2")
    prefix = render_prefix(user_id)
    projects: dict[str, dict[str, Any]] = {}

    for page in paginator.paginate(Bucket=_bucket(), Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rest = key[len(prefix):]
            parts = rest.split("/")
            if len(parts) < 3:
                continue
            project, kind = parts[0], parts[1]
            if kind not in RENDER_KINDS:
                continue

            entry = projects.setdefault(
                project,
                {
                    "project": project,
                    "image_count": 0,
                    "video_count": 0,
                    "cover_key": None,
                    "last_modified": obj["LastModified"],
                },
            )

            if is_thumb(key):
                # Thumbnails are presentation, not inventory: they must not
                # inflate counts, but any one of them makes a fine cover.
                if entry["cover_key"] is None:
                    entry["cover_key"] = key
                continue

            if kind == "images":
                entry["image_count"] += 1
            else:
                entry["video_count"] += 1

            if obj["LastModified"] > entry["last_modified"]:
                entry["last_modified"] = obj["LastModified"]

    result = [p for p in projects.values() if p["image_count"] or p["video_count"]]
    result.sort(key=lambda p: p["last_modified"], reverse=True)
    return result


def list_renders(user_id: str, project: str, kind: str = "images") -> list[dict[str, Any]]:
    if kind not in RENDER_KINDS:
        raise StorageError(f"Unknown render kind '{kind}'")
    slug = sanitize_project_slug(project)

    client = public_client()
    paginator = client.get_paginator("list_objects_v2")
    prefix = render_prefix(user_id, slug, kind)
    available: set[str] = set()
    items: list[dict[str, Any]] = []

    for page in paginator.paginate(Bucket=_bucket(), Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            available.add(key)
            if is_thumb(key):
                continue
            items.append(
                {
                    "key": key,
                    "filename": key.rsplit("/", 1)[-1],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                }
            )

    # A thumbnail can be legitimately absent — its upload is best-effort so a
    # failed thumb never costs the render. The client falls back to the full
    # image, so report absence rather than handing out a URL that 404s.
    for item in items:
        thumb = thumb_key_for(item["key"])
        item["thumb_key"] = thumb if thumb in available else None

    items.sort(key=lambda i: i["last_modified"], reverse=True)
    return items


def head_render(key: str, user_id: str) -> dict[str, Any]:
    """Render settings recorded at upload time. One HEAD, on demand — keeping
    it out of the listing is what lets the grid stay a single request."""
    assert_owned(key, user_id)
    response = public_client().head_object(Bucket=_bucket(), Key=key)
    return {
        "size": response.get("ContentLength", 0),
        "last_modified": response.get("LastModified"),
        "metadata": response.get("Metadata", {}) or {},
    }


def delete_render(key: str, user_id: str):
    """Delete a render and its thumbnail together, so the Library can't be left
    showing a preview of something that no longer exists."""
    assert_owned(key, user_id)
    client = public_client()
    client.delete_object(Bucket=_bucket(), Key=key)
    try:
        client.delete_object(Bucket=_bucket(), Key=thumb_key_for(key))
    except Exception as e:
        logger.warning(f"Could not delete thumbnail for {key}: {e}")
    logger.info(f"Deleted render {key}")


def presign_view(key: str, ttl: int = PRESIGN_TTL_SECONDS) -> str:
    """Presign a GET for the browser to display or download a render."""
    return public_client().generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": _bucket(), "Key": key},
        ExpiresIn=ttl,
    )


def _attachment_disposition(filename: str) -> str:
    """Content-Disposition value that makes a browser save rather than display.

    Two filename forms per RFC 6266: a plain ASCII one every client understands,
    and the RFC 5987 `filename*` that carries the real name when it has accents
    or spaces. Modern browsers prefer the latter and ignore the former.
    """
    ascii_name = (
        unicodedata.normalize("NFKD", filename)
        .encode("ascii", "ignore")
        .decode()
        .replace('"', "")
        .replace("\\", "")
        .strip()
    ) or "render.png"
    return (
        f'attachment; filename="{ascii_name}"; '
        f"filename*=UTF-8''{quote(filename, safe='')}"
    )


def presign_render_download(
    key: str, filename: str, ttl: int = PRESIGN_TTL_SECONDS
) -> str:
    """Presign a GET that downloads the render instead of displaying it.

    A separate URL from presign_view because `<a download>` is silently ignored
    cross-origin, and renders are fetched straight from RustFS — so the only
    thing that can force a save-to-disk is the response's own
    Content-Disposition, which a presigned URL overrides per request.
    """
    return public_client().generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": _bucket(),
            "Key": key,
            "ResponseContentDisposition": _attachment_disposition(filename),
        },
        ExpiresIn=ttl,
    )


def presign_thumb_put(key: str, ttl: int = PRESIGN_TTL_SECONDS) -> str:
    """Presign the thumbnail PUT handed to the instance. Small enough to never
    need multipart, so this stays a single signed URL."""
    return public_client().generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": _bucket(), "Key": key},
        ExpiresIn=ttl,
    )


def create_render_upload(key: str, metadata: dict[str, str] = None) -> dict[str, str]:
    """Start a multipart upload for a render, recording its settings as object
    metadata so the Library can show how a frame was made without a side table."""
    response = public_client().create_multipart_upload(
        Bucket=_bucket(),
        Key=key,
        ContentType="image/png",
        Metadata={k: str(v) for k, v in (metadata or {}).items()},
    )
    logger.info(f"Started render upload {response['UploadId']} for {key}")
    return {"uploadId": response["UploadId"], "key": key}


def presign_save(key: str, ttl: int = 12 * 3600) -> str:
    """
    Presign a PUT for the in-Blender addon to save back to.

    Long TTL and passed as an env var at launch, because the emergency save fires
    exactly when the engine is unreachable — so the addon cannot ask for a URL then.
    ContentLength is deliberately not pinned: the saved size is unknown at launch.
    """
    return internal_client().generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": _bucket(), "Key": key},
        ExpiresIn=ttl,
    )
