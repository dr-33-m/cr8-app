"""
Storage service tests — no network, no RustFS required.

Focus is the ownership gate and filename handling, because those are the security
boundary: every key that reaches boto3 is client-supplied, and the only thing
stopping user A from writing into user B's prefix is assert_owned.

Run:  venv/bin/python -m pytest tests/test_storage_service.py -v
"""

import pytest

from app.services import storage_service as s
from app.services.storage_service import StorageError

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


class TestAssertOwned:
    def test_accepts_own_key(self):
        key = f"users/{USER_A}/scene.blend"
        assert s.assert_owned(key, USER_A) == key

    def test_rejects_other_users_key(self):
        """The IDOR case: A's key presented with B's identity."""
        with pytest.raises(StorageError):
            s.assert_owned(f"users/{USER_A}/scene.blend", USER_B)

    def test_rejects_traversal(self):
        with pytest.raises(StorageError):
            s.assert_owned(f"users/{USER_A}/../{USER_B}/scene.blend", USER_A)

    def test_rejects_prefix_confusion(self):
        """A user id that merely starts with another's must not match."""
        with pytest.raises(StorageError):
            s.assert_owned(f"users/{USER_A}extra/scene.blend", USER_A)

    def test_rejects_bare_filename(self):
        with pytest.raises(StorageError):
            s.assert_owned("scene.blend", USER_A)


class TestSanitizeFilename:
    def test_accepts_plain_name(self):
        assert s.sanitize_filename("my scene_v2.blend") == "my scene_v2.blend"

    def test_strips_directory_components(self):
        assert s.sanitize_filename("/etc/passwd/scene.blend") == "scene.blend"
        assert s.sanitize_filename("..\\..\\scene.blend") == "scene.blend"

    def test_rejects_non_blend(self):
        with pytest.raises(StorageError):
            s.sanitize_filename("payload.sh")

    def test_rejects_empty(self):
        with pytest.raises(StorageError):
            s.sanitize_filename("   ")

    def test_rejects_exotic_characters(self):
        with pytest.raises(StorageError):
            s.sanitize_filename("scene;rm -rf.blend")

    def test_build_key_is_scoped_to_user(self):
        assert s.build_key(USER_A, "scene.blend") == f"users/{USER_A}/scene.blend"


class TestAssertSize:
    def test_accepts_normal_size(self):
        s.assert_size(1024)

    def test_rejects_zero_and_negative(self):
        with pytest.raises(StorageError):
            s.assert_size(0)
        with pytest.raises(StorageError):
            s.assert_size(-1)

    def test_rejects_over_cap(self):
        with pytest.raises(StorageError):
            s.assert_size(s.MAX_BLEND_BYTES + 1)


class TestMultipartOwnership:
    """
    Every multipart entry point must gate on ownership. sign-part is the sharpest:
    an unguarded one lets a caller write into another user's prefix given only
    that user's key and an uploadId.
    """

    @pytest.mark.parametrize(
        "call",
        [
            lambda key, uid: s.presign_part(key, "upload-id", 1, uid),
            lambda key, uid: s.list_parts(key, "upload-id", uid),
            lambda key, uid: s.complete_multipart_upload(key, "upload-id", [], uid),
            lambda key, uid: s.abort_multipart_upload(key, "upload-id", uid),
        ],
        ids=["sign_part", "list_parts", "complete", "abort"],
    )
    def test_rejects_foreign_key(self, call):
        with pytest.raises(StorageError):
            call(f"users/{USER_A}/scene.blend", USER_B)


class TestThresholds:
    def test_single_put_threshold_stays_under_cloudflare_cap(self):
        """
        Regression guard for the MiB-vs-MB trap: the tunnel caps request bodies at
        100 MB (100_000_000), and anything on the single-PUT path must fit under it.
        Uppy's own default is 100 MiB (104_857_600) — which would 413.
        """
        assert s.SINGLE_PUT_MAX_BYTES < 100_000_000

    def test_single_put_rejects_multipart_sized_file(self):
        with pytest.raises(StorageError):
            s.presign_upload(USER_A, "big.blend", s.SINGLE_PUT_MAX_BYTES + 1)

    def test_part_number_is_bounded(self):
        """
        Bounds a well-behaved multipart upload near MAX_BLEND_BYTES, since S3
        requires >=5MB parts. Not airtight — nothing signs each part's length —
        but it stops an unbounded part count.
        """
        key = f"users/{USER_A}/big.blend"
        for bad in (0, -1, s.MAX_PART_NUMBER + 1):
            with pytest.raises(StorageError):
                s.presign_part(key, "upload-id", bad, USER_A)
