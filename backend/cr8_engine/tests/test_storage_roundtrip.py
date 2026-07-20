"""
End-to-end storage round-trip against a real (mocked) S3 server.

This exercises the actual HTTP flow a browser performs — presign here, PUT there —
rather than trusting the shape of the boto3 calls. It catches wrong parameter
names, bad presign params, and multipart sequencing errors.

Scope limit worth being honest about: moto is an S3 mock, not RustFS. Passing here
proves our S3 usage is correct, NOT that RustFS accepts it. The RustFS-specific
risks (path-style addressing, s3v4, CORS, the Cloudflare body cap) still need a
real endpoint — see the plan's verification section.

Run:  venv/bin/python -m pytest tests/test_storage_roundtrip.py -v
"""

import pytest

pytest.importorskip("moto", reason="moto not installed — dev-only dependency")

import boto3
import requests
from moto.server import ThreadedMotoServer

from app.services import config as config_module
from app.services import storage_service as s

USER = "aaaaaaaa-1111-1111-1111-111111111111"
BUCKET = "cr8-xyz"


@pytest.fixture(scope="module")
def s3_endpoint():
    server = ThreadedMotoServer(port=0)
    server.start()
    host, port = server.get_host_and_port()
    yield f"http://{host}:{port}"
    server.stop()


@pytest.fixture(autouse=True)
def storage_env(s3_endpoint, monkeypatch):
    monkeypatch.setenv("RUSTFS_PUBLIC_ENDPOINT", s3_endpoint)
    monkeypatch.setenv("RUSTFS_INTERNAL_ENDPOINT", s3_endpoint)
    monkeypatch.setenv("RUSTFS_ACCESS_KEY", "testing")
    monkeypatch.setenv("RUSTFS_SECRET_KEY", "testing")
    monkeypatch.setenv("RUSTFS_BUCKET", BUCKET)
    config_module.DeploymentConfig.reset()
    s.reset_clients()

    client = boto3.client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        region_name="us-east-1",
    )
    try:
        client.create_bucket(Bucket=BUCKET)
    except client.exceptions.BucketAlreadyOwnedByYou:
        pass
    yield
    config_module.DeploymentConfig.reset()
    s.reset_clients()


def test_single_put_roundtrip():
    """Presign, PUT the bytes as a browser would, then see it in the listing."""
    body = b"blender" * 100
    presigned = s.presign_upload(USER, "scene.blend", len(body))

    response = requests.put(presigned["upload_url"], data=body, timeout=30)
    assert response.status_code == 200, response.text

    files = s.list_blend_files(USER)
    assert [f["filename"] for f in files] == ["scene.blend"]
    assert files[0]["size"] == len(body)


def test_single_put_url_commits_the_client_to_a_length():
    """
    We can prove boto3 puts content-length in SignedHeaders. We CANNOT prove here
    that a mismatched body is rejected: moto does not validate signatures at all
    (it accepts a corrupted signature, and an unsigned PUT, with 200).

    So the single-PUT size cap holds only if RustFS actually verifies the s3v4
    signature. Its docs list SignatureDoesNotMatch as a common error, which
    implies it does — but that is inference, not evidence.

    ⚠️ Verify against real RustFS: presign for 10 bytes, PUT 5000, expect 4xx.
    If it returns 200, the single-PUT size cap is fiction and needs a real quota.
    """
    from urllib.parse import parse_qs, urlparse

    url = s.presign_upload(USER, "liar.blend", 10)["upload_url"]
    signed = parse_qs(urlparse(url).query)["X-Amz-SignedHeaders"][0]
    assert "content-length" in signed


def test_multipart_roundtrip():
    """
    The path a 1GB upload actually takes. Parts must be >=5MB except the last,
    so this uses two real 5MB parts rather than toy data.
    """
    part_size = 5 * 1024 * 1024
    parts_data = [b"a" * part_size, b"b" * 1024]

    created = s.create_multipart_upload(USER, "big.blend")
    key, upload_id = created["key"], created["uploadId"]

    uploaded = []
    for i, chunk in enumerate(parts_data, start=1):
        url = s.presign_part(key, upload_id, i, USER)
        r = requests.put(url, data=chunk, timeout=60)
        assert r.status_code == 200, r.text
        # The browser reads ETag off the response header — this is exactly what
        # the bucket's CORS policy must expose, or completion cannot be built.
        assert r.headers.get("ETag"), "no ETag returned for part"
        uploaded.append({"PartNumber": i, "ETag": r.headers["ETag"]})

    listed = s.list_parts(key, upload_id, USER)
    assert [p["PartNumber"] for p in listed] == [1, 2]

    s.complete_multipart_upload(key, upload_id, uploaded, USER)

    files = {f["filename"]: f for f in s.list_blend_files(USER)}
    assert files["big.blend"]["size"] == sum(len(c) for c in parts_data)


def test_multipart_abort_leaves_nothing():
    created = s.create_multipart_upload(USER, "abandoned.blend")
    key, upload_id = created["key"], created["uploadId"]

    url = s.presign_part(key, upload_id, 1, USER)
    requests.put(url, data=b"x" * (5 * 1024 * 1024), timeout=60)

    s.abort_multipart_upload(key, upload_id, USER)

    assert "abandoned.blend" not in {f["filename"] for f in s.list_blend_files(USER)}


def test_presigned_download_returns_the_bytes():
    """The GET that launch-blender.sh will curl onto the instance."""
    body = b"scene-data"
    presigned = s.presign_upload(USER, "download-me.blend", len(body))
    requests.put(presigned["upload_url"], data=body, timeout=30)

    r = requests.get(s.presign_download(presigned["key"]), timeout=30)
    assert r.status_code == 200
    assert r.content == body


def test_listing_is_scoped_to_the_user():
    """User A's files must never appear in user B's listing."""
    other = "bbbbbbbb-2222-2222-2222-222222222222"
    body = b"mine"
    p = s.presign_upload(USER, "private.blend", len(body))
    requests.put(p["upload_url"], data=body, timeout=30)

    assert s.list_blend_files(other) == []
