"""
Render library listing against a real (mocked) S3 server.

The listing logic is where renders, thumbnails and the videos prefix all have to
agree — counts that include thumbnails, or a thumbnail that surfaces as its own
gallery item, are the kind of bug that only shows up with real objects in a real
bucket. Same scope caveat as test_storage_roundtrip: moto is an S3 mock, not
RustFS.

Run:  venv/bin/python -m pytest tests/test_render_library.py -v
"""

import pytest

pytest.importorskip("moto", reason="moto not installed — dev-only dependency")

import boto3
import requests
from moto.server import ThreadedMotoServer

from app.services import config as config_module
from app.services import storage_service as s

USER = "bbbbbbbb-2222-2222-2222-222222222222"
OTHER = "cccccccc-3333-3333-3333-333333333333"
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

    # Clean slate — the moto server is module-scoped and shared across tests.
    existing = client.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    for obj in existing:
        client.delete_object(Bucket=BUCKET, Key=obj["Key"])

    yield client

    config_module.DeploymentConfig.reset()
    s.reset_clients()


def put(client, key, body=b"x"):
    client.put_object(Bucket=BUCKET, Key=key, Body=body)


def seed_render(client, user, project, name, with_thumb=True):
    key = s.build_render_key(user, project, name)
    put(client, key, b"pretend-png")
    if with_thumb:
        put(client, s.thumb_key_for(key), b"pretend-jpg")
    return key


class TestListRenderProjects:
    def test_groups_by_project_and_counts_images(self, storage_env):
        seed_render(storage_env, USER, "bedroom_scene", "shot-01")
        seed_render(storage_env, USER, "bedroom_scene", "shot-02")
        seed_render(storage_env, USER, "archviz", "shot-01")

        projects = {p["project"]: p for p in s.list_render_projects(USER)}
        assert projects["bedroom_scene"]["image_count"] == 2
        assert projects["archviz"]["image_count"] == 1

    def test_thumbnails_do_not_inflate_counts(self, storage_env):
        """Each render seeds a thumbnail too — counting those would double
        every number the library shows."""
        seed_render(storage_env, USER, "bedroom_scene", "shot-01", with_thumb=True)

        projects = {p["project"]: p for p in s.list_render_projects(USER)}
        assert projects["bedroom_scene"]["image_count"] == 1

    def test_thumbnail_becomes_the_cover(self, storage_env):
        key = seed_render(storage_env, USER, "bedroom_scene", "shot-01")

        projects = {p["project"]: p for p in s.list_render_projects(USER)}
        assert projects["bedroom_scene"]["cover_key"] == s.thumb_key_for(key)

    def test_another_users_renders_are_not_listed(self, storage_env):
        seed_render(storage_env, USER, "mine", "shot-01")
        seed_render(storage_env, OTHER, "theirs", "shot-01")

        names = {p["project"] for p in s.list_render_projects(USER)}
        assert names == {"mine"}

    def test_empty_when_the_user_has_no_renders(self, storage_env):
        assert s.list_render_projects(USER) == []


class TestListRenders:
    def test_returns_renders_without_their_thumbnails(self, storage_env):
        seed_render(storage_env, USER, "proj", "shot-01")
        seed_render(storage_env, USER, "proj", "shot-02")

        items = s.list_renders(USER, "proj")
        filenames = sorted(i["filename"] for i in items)
        assert filenames == ["shot-01.png", "shot-02.png"]

    def test_pairs_each_render_with_its_thumbnail(self, storage_env):
        key = seed_render(storage_env, USER, "proj", "shot-01")

        item = s.list_renders(USER, "proj")[0]
        assert item["thumb_key"] == s.thumb_key_for(key)

    def test_missing_thumbnail_is_reported_as_none(self, storage_env):
        """The thumbnail upload is best-effort, so its absence is normal. The
        listing must say so rather than hand out a URL that 404s."""
        seed_render(storage_env, USER, "proj", "no-thumb", with_thumb=False)

        item = s.list_renders(USER, "proj")[0]
        assert item["thumb_key"] is None

    def test_videos_kind_is_empty_but_valid(self, storage_env):
        seed_render(storage_env, USER, "proj", "shot-01")
        assert s.list_renders(USER, "proj", kind="videos") == []

    def test_rejects_unknown_kind(self, storage_env):
        with pytest.raises(s.StorageError):
            s.list_renders(USER, "proj", kind="../../etc")


class TestDeleteRender:
    def test_removes_the_render_and_its_thumbnail(self, storage_env):
        key = seed_render(storage_env, USER, "proj", "shot-01")

        s.delete_render(key, USER)

        remaining = storage_env.list_objects_v2(Bucket=BUCKET).get("Contents", [])
        assert remaining == []

    def test_refuses_to_delete_another_users_render(self, storage_env):
        key = seed_render(storage_env, OTHER, "theirs", "shot-01")

        with pytest.raises(s.StorageError):
            s.delete_render(key, USER)

        remaining = storage_env.list_objects_v2(Bucket=BUCKET).get("Contents", [])
        assert len(remaining) == 2  # render + thumb, untouched


class TestRenderUploadRoundTrip:
    def test_presigned_parts_upload_and_complete(self, storage_env):
        """The real flow: engine creates the upload and signs parts, the
        instance PUTs bytes to those URLs, the engine completes from ETags."""
        key = s.build_render_key(USER, "proj", "roundtrip")
        created = s.create_render_upload(key, metadata={"engine": "CYCLES"})
        upload_id = created["uploadId"]

        url = s.presign_part(key, upload_id, 1, USER)
        body = b"a" * (5 * 1024 * 1024)
        response = requests.put(url, data=body)
        assert response.status_code == 200

        etag = response.headers["ETag"]
        s.complete_multipart_upload(
            key, upload_id, [{"PartNumber": 1, "ETag": etag}], USER
        )

        stored = storage_env.get_object(Bucket=BUCKET, Key=key)
        assert stored["Body"].read() == body

    def test_metadata_survives_the_upload(self, storage_env):
        key = s.build_render_key(USER, "proj", "with-meta")
        created = s.create_render_upload(
            key, metadata={"engine": "CYCLES", "resolution": "4k", "camera": "Cam"}
        )
        url = s.presign_part(key, created["uploadId"], 1, USER)
        response = requests.put(url, data=b"b" * (5 * 1024 * 1024))
        s.complete_multipart_upload(
            key,
            created["uploadId"],
            [{"PartNumber": 1, "ETag": response.headers["ETag"]}],
            USER,
        )

        meta = s.head_render(key, USER)
        assert meta["metadata"]["engine"] == "CYCLES"
        assert meta["metadata"]["resolution"] == "4k"

    def test_thumbnail_presigned_put_works(self, storage_env):
        key = s.build_render_key(USER, "proj", "thumbed")
        url = s.presign_thumb_put(s.thumb_key_for(key))

        response = requests.put(url, data=b"jpeg-bytes")
        assert response.status_code == 200

        stored = storage_env.get_object(Bucket=BUCKET, Key=s.thumb_key_for(key))
        assert stored["Body"].read() == b"jpeg-bytes"

    def test_presigned_view_url_is_readable(self, storage_env):
        key = seed_render(storage_env, USER, "proj", "viewable", with_thumb=False)

        response = requests.get(s.presign_view(key))
        assert response.status_code == 200
        assert response.content == b"pretend-png"
