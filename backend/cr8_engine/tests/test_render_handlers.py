"""
Engine-side render orchestration tests.

Covers the contract the frontend depends on (NO_TARGET rather than a 500 when a
project has no cloud target), the validation of settings that end up steering
bpy property assignments, and the invariant that a multipart upload is always
resolved — completed on success, aborted on failure — so a failed render never
leaves a dangling upload holding storage.

Run:  venv/bin/python -m pytest tests/test_render_handlers.py -v
"""

import os

import pytest

os.environ.setdefault("LOGTO_INTERNAL_SECRET", "test-secret-not-for-real-use")

from app.realtime_engine.namespaces.browser.render_handlers import RenderHandlersMixin

USER_ID = "dddddddd-4444-4444-4444-444444444444"
BLEND_KEY = f"users/{USER_ID}/Bedroom Scene.blend"


class FakeBlenderNamespace:
    """Stands in for the /blender namespace. Records the command it was asked to
    send so the params crossing the wire can be asserted on."""

    def __init__(self, response=None):
        self.response = response
        self.sent = []

    async def request_and_wait(self, username, command_data, timeout=60.0):
        self.sent.append(command_data)
        return self.response


class FakeServer:
    def __init__(self, blender_ns):
        self.namespace_handlers = {'/blender': blender_ns}


class FakeNamespace(RenderHandlersMixin):
    """Minimal host for the mixin — real emit/session plumbing replaced with
    recording, so these tests exercise the handler and nothing else."""

    def __init__(self, session, blender_ns=None, user_id=USER_ID):
        import logging
        self.logger = logging.getLogger(__name__)
        self._session = session
        self._user_id = user_id
        self.emitted = []
        self.server = FakeServer(blender_ns or FakeBlenderNamespace())

    async def get_session(self, sid):
        return self._session

    async def _resolve_db_user_id(self, logto_id):
        return self._user_id

    async def emit(self, event, data, to=None):
        self.emitted.append((event, data))

    def last_error_code(self):
        for event, data in reversed(self.emitted):
            error = (data.get('payload') or {}).get('error')
            if error:
                return error.get('code')
        return None

    def last_result(self):
        for event, data in reversed(self.emitted):
            payload = data.get('payload') or {}
            if payload.get('status') == 'success':
                return payload.get('data') or {}
        return None


def make_session(**overrides):
    session = {
        'username': 'alice',
        'logto_id': 'logto-alice',
        'blender_sid': 'blender-sid-1',
        'blend_object_key': BLEND_KEY,
    }
    session.update(overrides)
    return session


@pytest.fixture(autouse=True)
def storage_stubs(monkeypatch):
    """Stub only the S3 calls. Key building, sanitisation and ownership run for
    real — they are the part worth exercising here."""
    from app.services import storage_service as s

    state = {'created': [], 'completed': [], 'aborted': []}

    def fake_create(key, metadata=None):
        state['created'].append((key, metadata))
        return {'uploadId': 'upload-1', 'key': key}

    monkeypatch.setattr(s, 'create_render_upload', fake_create)
    monkeypatch.setattr(s, 'presign_part', lambda k, u, i, uid: f"https://put/{i}")
    monkeypatch.setattr(s, 'presign_thumb_put', lambda k, ttl=3600: "https://put/thumb")
    monkeypatch.setattr(
        s, 'complete_multipart_upload',
        lambda k, u, p, uid: state['completed'].append(k) or {'location': ''})
    monkeypatch.setattr(
        s, 'abort_multipart_upload',
        lambda k, u, uid: state['aborted'].append(k))
    return state


class TestGuardRails:
    async def test_unsaved_project_reports_no_target(self):
        """The contract the frontend turns into a Save As prompt. A 500 or a
        generic failure here would strand the user with no way forward."""
        ns = FakeNamespace(make_session(blend_object_key=None))

        await ns.on_render_image('sid', {'message_id': 'm1'})

        assert ns.last_error_code() == 'NO_TARGET'

    async def test_no_upload_is_started_when_there_is_no_target(self, storage_stubs):
        ns = FakeNamespace(make_session(blend_object_key=None))

        await ns.on_render_image('sid', {'message_id': 'm1'})

        assert storage_stubs['created'] == []

    async def test_disconnected_blender_is_reported_before_any_upload(self, storage_stubs):
        ns = FakeNamespace(make_session(blender_sid=None))

        await ns.on_render_image('sid', {'message_id': 'm1'})

        assert ns.last_error_code() == 'BLENDER_DISCONNECTED'
        assert storage_stubs['created'] == []

    async def test_unresolvable_user_is_reported(self):
        ns = FakeNamespace(make_session(), user_id=None)

        await ns.on_render_image('sid', {'message_id': 'm1'})

        assert ns.last_error_code() == 'AUTH_ERROR'

    @pytest.mark.parametrize("field,value", [
        ('engine', 'OCTANE'),
        ('resolution', '8k'),
        ('aspect', '99:1'),
    ])
    async def test_rejects_unknown_settings(self, field, value, storage_stubs):
        """These steer bpy property assignments in the addon — a clear error
        here beats a half-configured render there."""
        ns = FakeNamespace(make_session())

        await ns.on_render_image('sid', {'message_id': 'm1', field: value})

        assert ns.last_error_code() == 'VALIDATION_ERROR'
        assert storage_stubs['created'] == []


class TestSuccessPath:
    async def test_completes_the_upload_and_reports_the_key(self, storage_stubs):
        blender = FakeBlenderNamespace(response={
            'ok': True,
            'parts': [{'PartNumber': 1, 'ETag': 'etag-1'}],
            'thumb_ok': True,
            'width': 1920,
            'height': 1080,
            'message': 'Render saved',
        })
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {'message_id': 'm1', 'camera': 'Camera'})

        result = ns.last_result()
        assert result['ok'] is True
        assert result['project'] == 'Bedroom Scene'
        assert result['key'].startswith(
            f"users/{USER_ID}/renders/Bedroom Scene/images/")
        assert len(storage_stubs['completed']) == 1
        assert storage_stubs['aborted'] == []

    async def test_sends_a_populated_multipart_descriptor_to_the_addon(self):
        """The silent-drop trap: if this arrives empty the render succeeds and
        uploads nowhere, with only a log warning to show for it."""
        blender = FakeBlenderNamespace(response={
            'ok': True, 'parts': [{'PartNumber': 1, 'ETag': 'e'}], 'thumb_ok': True,
        })
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {'message_id': 'm1', 'camera': 'Camera'})

        params = blender.sent[0]['params']
        assert params['multipart']['upload_id'] == 'upload-1'
        assert len(params['multipart']['part_urls']) == 4
        assert params['multipart']['part_size'] > 0
        assert params['thumb_url'] == 'https://put/thumb'

    async def test_targets_the_render_addon_not_the_router(self):
        blender = FakeBlenderNamespace(response={
            'ok': True, 'parts': [{'PartNumber': 1, 'ETag': 'e'}],
        })
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {'message_id': 'm1'})

        assert blender.sent[0]['addon_id'] == 'cr8_render'
        assert blender.sent[0]['command'] == 'render_image'

    async def test_records_settings_as_object_metadata(self, storage_stubs):
        blender = FakeBlenderNamespace(response={
            'ok': True, 'parts': [{'PartNumber': 1, 'ETag': 'e'}],
        })
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {
            'message_id': 'm1', 'camera': 'Kitchen',
            'engine': 'CYCLES', 'resolution': '4k', 'aspect': '1:1',
        })

        _key, metadata = storage_stubs['created'][0]
        assert metadata['engine'] == 'CYCLES'
        assert metadata['resolution'] == '4k'
        assert metadata['camera'] == 'Kitchen'

    async def test_thumb_key_is_omitted_when_the_thumbnail_did_not_upload(self):
        blender = FakeBlenderNamespace(response={
            'ok': True, 'parts': [{'PartNumber': 1, 'ETag': 'e'}], 'thumb_ok': False,
        })
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {'message_id': 'm1'})

        assert ns.last_result()['thumb_key'] is None


class TestFailurePath:
    async def test_aborts_the_upload_when_the_addon_reports_failure(self, storage_stubs):
        blender = FakeBlenderNamespace(response={
            'status': 'error', 'ok': False, 'message': 'Xorg died',
        })
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {'message_id': 'm1'})

        created_key = storage_stubs['created'][0][0]
        assert storage_stubs['aborted'] == [created_key]
        assert storage_stubs['completed'] == []

    async def test_surfaces_the_addons_own_reason(self):
        blender = FakeBlenderNamespace(response={
            'status': 'error', 'ok': False,
            'message': "Camera 'Kitchen' is not in this scene",
        })
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {'message_id': 'm1', 'camera': 'Kitchen'})

        _event, data = ns.emitted[-1]
        assert "Kitchen" in data['payload']['data']['message']

    async def test_timeout_aborts_the_upload(self, storage_stubs):
        """request_and_wait returns None on timeout — the upload must still be
        cleaned up rather than left dangling."""
        blender = FakeBlenderNamespace(response=None)
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {'message_id': 'm1'})

        assert len(storage_stubs['aborted']) == 1
        assert storage_stubs['completed'] == []

    async def test_reports_failure_when_parts_are_missing(self, storage_stubs):
        """ok without parts can't be completed — treat it as a failure rather
        than calling complete_multipart_upload with nothing."""
        blender = FakeBlenderNamespace(response={'ok': True, 'parts': []})
        ns = FakeNamespace(make_session(), blender_ns=blender)

        await ns.on_render_image('sid', {'message_id': 'm1'})

        assert storage_stubs['completed'] == []
        assert len(storage_stubs['aborted']) == 1
