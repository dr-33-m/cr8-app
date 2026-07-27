"""
Cloud upload for rendered files.

Deliberately a local copy of the router's multipart loop rather than an import
from it. Reaching across extensions would mean
`bl_ext.user_default.cr8_router.ws.websocket_handler`, a path that
depends on the repo name the extension was installed under and couples two
extensions' load order. Thirty lines of "PUT this file to these URLs" is the
cheaper of the two.

No credentials ever reach the instance — every URL here is pre-signed by the
engine.
"""

import logging

logger = logging.getLogger(__name__)

# Matches the engine's SAVE_PART_SIZE_BYTES rationale: RustFS sits behind a
# Cloudflare tunnel that caps request bodies at ~100MB, and the instance has no
# path around it.
PART_TIMEOUT_SECONDS = 600


def upload_multipart(filepath: str, multipart: dict):
    """Upload a file as pre-signed parts. Returns (ok, {"parts": [...]}) —
    the engine completes the upload from those ETags."""
    part_size = multipart.get('part_size')
    part_urls = multipart.get('part_urls') or []
    if not part_size or not part_urls:
        return False, {'message': 'Missing multipart parameters'}

    try:
        import requests
        parts = []
        with open(filepath, 'rb') as f:
            index = 0
            while True:
                chunk = f.read(part_size)
                if not chunk:
                    break
                if index >= len(part_urls):
                    return False, {'message': 'Render is larger than the upload can handle'}
                resp = requests.put(
                    part_urls[index], data=chunk, timeout=PART_TIMEOUT_SECONDS)
                if resp.status_code != 200:
                    return False, {
                        'message': f"Part {index + 1} failed (status {resp.status_code})"}
                etag = resp.headers.get('ETag') or resp.headers.get('Etag')
                parts.append({'PartNumber': index + 1, 'ETag': etag})
                index += 1
        if not parts:
            return False, {'message': 'Nothing to upload'}
        logger.info(f"Uploaded {filepath} in {len(parts)} part(s)")
        return True, {'parts': parts}
    except Exception as e:
        logger.error(f"Multipart upload failed: {e}")
        return False, {'message': f"Upload failed: {e}"}


def upload_single(filepath: str, url: str) -> bool:
    """Single PUT, used for thumbnails — always well under the tunnel's cap.

    Never fatal to a render: losing a thumbnail costs a placeholder in the
    library, while the render itself is already safely uploaded.
    """
    if not url:
        return False
    try:
        import requests
        with open(filepath, 'rb') as f:
            resp = requests.put(url, data=f, timeout=PART_TIMEOUT_SECONDS)
        if resp.status_code != 200:
            logger.warning(f"Thumbnail upload failed (status {resp.status_code})")
            return False
        return True
    except Exception as e:
        logger.warning(f"Thumbnail upload failed: {e}")
        return False
