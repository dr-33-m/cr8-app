"""
Render storage key tests — no network, no RustFS required.

Same focus as test_storage_service.py: the ownership gate and name handling are
the security boundary. Renders widen the key space (a project folder and a media
kind now sit between the user prefix and the leaf), so each new segment gets its
own hostile-input coverage.

Run:  venv/bin/python -m pytest tests/test_render_storage.py -v
"""

import pytest

from app.services import storage_service as s
from app.services.storage_service import StorageError

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


class TestSanitizeRenderName:
    def test_accepts_plain_name(self):
        assert s.sanitize_render_name("20260721-120000_Camera") == "20260721-120000_Camera"

    def test_strips_path_structure(self):
        """Path separators are stripped, not rejected — same defence as
        sanitize_filename. What matters is that only a leaf survives."""
        assert s.sanitize_render_name("../../etc/passwd") == "passwd"
        assert s.sanitize_render_name("a/b/c") == "c"

    def test_strips_a_supplied_extension(self):
        """The extension is added by build_render_key, so a name can't smuggle
        in a different content type."""
        assert s.sanitize_render_name("shot.png") == "shot"

    def test_rejects_empty_and_dots(self):
        for bad in ("", "   ", ".", ".."):
            with pytest.raises(StorageError):
                s.sanitize_render_name(bad)

    def test_rejects_shell_and_control_characters(self):
        for bad in ("a$b", "a;b", "a\nb", "a`b", "a|b"):
            with pytest.raises(StorageError):
                s.sanitize_render_name(bad)

    def test_rejects_overlong_name(self):
        with pytest.raises(StorageError):
            s.sanitize_render_name("x" * 300)


class TestSanitizeProjectSlug:
    def test_accepts_name_with_spaces(self):
        assert s.sanitize_project_slug("Bedroom Scene") == "Bedroom Scene"

    def test_rejects_traversal(self):
        """Unlike a render name this is NOT stripped to a leaf — a project slug
        arrives as a route param, and silently rewriting it would send the user
        to a different project than the URL says."""
        for bad in ("../..", "a/b", "..", ""):
            with pytest.raises(StorageError):
                s.sanitize_project_slug(bad)


class TestProjectSlugFromBlendKey:
    def test_derives_slug_from_blend_key(self):
        key = f"users/{USER_A}/Bedroom Scene.blend"
        assert s.project_slug_from_blend_key(key) == "Bedroom Scene"

    def test_is_case_insensitive_about_the_extension(self):
        key = f"users/{USER_A}/Archviz.BLEND"
        assert s.project_slug_from_blend_key(key) == "Archviz"


class TestBuildRenderKey:
    def test_lands_under_the_users_render_prefix(self):
        key = s.build_render_key(USER_A, "Bedroom Scene", "shot-01")
        assert key == f"users/{USER_A}/renders/Bedroom Scene/images/shot-01.png"

    def test_hostile_name_cannot_escape_the_prefix(self):
        key = s.build_render_key(USER_A, "proj", "../../../../etc/passwd")
        assert key.startswith(f"users/{USER_A}/renders/proj/images/")
        assert ".." not in key

    def test_rejects_unknown_kind(self):
        with pytest.raises(StorageError):
            s.build_render_key(USER_A, "proj", "shot", kind="secrets")

    def test_videos_kind_is_already_addressable(self):
        """The videos prefix exists now so animation output lands later without
        a migration or a re-listing scheme."""
        key = s.build_render_key(USER_A, "proj", "clip", kind="videos")
        assert key == f"users/{USER_A}/renders/proj/videos/clip.png"


class TestOwnership:
    def test_rejects_another_users_render_key(self):
        """The IDOR case, at the render layer."""
        key = s.build_render_key(USER_A, "proj", "shot")
        with pytest.raises(StorageError):
            s.assert_owned(key, USER_B)

    def test_accepts_own_render_key(self):
        key = s.build_render_key(USER_A, "proj", "shot")
        assert s.assert_owned(key, USER_A) == key


class TestThumbnailKeys:
    def test_thumb_is_derived_from_the_render_key(self):
        key = s.build_render_key(USER_A, "proj", "shot")
        assert s.thumb_key_for(key) == (
            f"users/{USER_A}/renders/proj/images/shot{s.THUMB_SUFFIX}"
        )

    def test_thumb_is_recognised_and_a_render_is_not(self):
        key = s.build_render_key(USER_A, "proj", "shot")
        assert s.is_thumb(s.thumb_key_for(key))
        assert not s.is_thumb(key)

    def test_thumb_stays_inside_the_owning_prefix(self):
        key = s.build_render_key(USER_A, "proj", "shot")
        assert s.assert_owned(s.thumb_key_for(key), USER_A)

    def test_blend_listing_is_unaffected_by_render_keys(self):
        """list_blend_files filters on the .blend suffix, so renders must never
        show up in the project browser."""
        key = s.build_render_key(USER_A, "proj", "shot")
        assert not key.lower().endswith(".blend")
        assert not s.thumb_key_for(key).lower().endswith(".blend")
