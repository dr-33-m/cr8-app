"""
Asserts the backend's closed ProvisionReason set and the frontend's
ERROR_REASONS map (studioLoadingMessages.ts) never drift apart — a reason
added to one side without the other used to fail silently at runtime
(bug #10 in the plan); this makes it fail CI instead.

Run:  venv/bin/python -m pytest tests/test_provisioning_error_taxonomy.py -v
"""

import re
from pathlib import Path

from app.services.provisioning.errors import ALL_REASONS

FRONTEND_FILE = (
    Path(__file__).resolve().parents[3] / "frontend" / "app" / "lib" / "studioLoadingMessages.ts"
)


def _frontend_error_reason_keys() -> set[str]:
    text = FRONTEND_FILE.read_text()
    match = re.search(r"export const ERROR_REASONS.*?=\s*{(.*?)^};", text, re.DOTALL | re.MULTILINE)
    assert match, "Could not locate ERROR_REASONS object in studioLoadingMessages.ts"
    body = match.group(1)
    return set(re.findall(r"^\s*(\w+):", body, re.MULTILINE))


def test_frontend_file_exists():
    assert FRONTEND_FILE.exists(), f"Expected {FRONTEND_FILE} to exist"


def test_every_backend_reason_has_a_frontend_message():
    frontend_keys = _frontend_error_reason_keys()
    missing = ALL_REASONS - frontend_keys
    assert not missing, f"ProvisionReason values with no ERROR_REASONS entry: {missing}"


def test_frontend_has_no_orphaned_keys_not_in_the_backend_taxonomy():
    """Not strictly required for correctness (an unused key is harmless), but
    catches copy-paste drift early."""
    frontend_keys = _frontend_error_reason_keys()
    orphaned = frontend_keys - ALL_REASONS
    assert not orphaned, f"ERROR_REASONS keys with no backend ProvisionReason: {orphaned}"
