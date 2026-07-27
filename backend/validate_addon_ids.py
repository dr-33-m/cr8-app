#!/usr/bin/env python3
"""
Validate that every cr8 addon identifier agrees across all four places it lives.

An addon's id is written down four times, and nothing enforces that they match:

  1. `id` in backend/<addon>/blender_manifest.toml   (Blender extension id)
  2. `addon_info.id` in backend/<addon>/addon_ai.json (what the router registers)
  3. the source directory name under backend/
  4. ADDON_IDS in frontend/app/lib/constants/addons.ts (what the browser sends)

They drifted before: cr8_sets answered to `multi_registry_assets` and cr8_router
to `blender_ai_router`. A mismatch fails at *runtime*, not at build time — the
router replies NO_HANDLERS and the command silently does nothing — so it can ship
unnoticed. This catches it without needing Blender.

Also checks the packaged zip root when a dist/ zip is present: the directory
inside the zip must equal the extension id, or Blender installs the addon under a
module path nothing can import.

Usage:
    python3 validate_addon_ids.py                 # from backend/
    python3 validate_addon_ids.py --repo-root ..  # from anywhere
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


def read_extension_id_and_version(manifest_toml: Path):
    """Pull id and version out of blender_manifest.toml without a TOML parser.

    Anchored to line starts so `schema_version` and `blender_version_min` cannot
    be mistaken for `version`.
    """
    text = manifest_toml.read_text()
    id_match = re.search(r'^id\s*=\s*"([^"]+)"', text, re.MULTILINE)
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return (
        id_match.group(1) if id_match else None,
        version_match.group(1) if version_match else None,
    )


def read_frontend_ids(constants_ts: Path):
    """Extract the id strings from the frontend ADDON_IDS constant."""
    if not constants_ts.exists():
        return None
    return set(re.findall(r'^\s*[A-Z_]+:\s*"([^"]+)"',
                          constants_ts.read_text(), re.MULTILINE))


def zip_root_dir(dist_dir: Path, addon_id: str):
    """Top-level directory inside the addon's packaged zip, if one exists."""
    zips = sorted(dist_dir.glob(f"{addon_id}_v*.zip")) if dist_dir.is_dir() else []
    if not zips:
        # Fall back to any zip — catches a zip still named after the old id.
        zips = sorted(dist_dir.glob("*.zip")) if dist_dir.is_dir() else []
    if not zips:
        return None, None
    zip_path = zips[-1]
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    root = names[0].split("/")[0] if names else None
    return root, zip_path.name


def validate(repo_root: Path) -> bool:
    backend = repo_root / "backend"
    constants_ts = repo_root / "frontend" / "app" / "lib" / "constants" / "addons.ts"

    if not backend.is_dir():
        print(f"❌ No backend/ directory under {repo_root}")
        return False

    addon_dirs = sorted(
        p for p in backend.iterdir()
        if p.is_dir() and (p / "blender_manifest.toml").exists()
    )
    if not addon_dirs:
        print(f"❌ Found no addons (no blender_manifest.toml) under {backend}")
        return False

    frontend_ids = read_frontend_ids(constants_ts)
    if frontend_ids is None:
        print(f"⚠️  Frontend constants not found at {constants_ts} — skipping that check\n")

    ok = True
    declared_ids = set()
    rows = []          # (cells, problems) — printed once widths are known

    for addon_dir in addon_dirs:
        name = addon_dir.name
        ext_id, version = read_extension_id_and_version(addon_dir / "blender_manifest.toml")

        ai_json = addon_dir / "addon_ai.json"
        if ai_json.exists():
            try:
                ai_id = json.load(open(ai_json))["addon_info"]["id"]
            except (json.JSONDecodeError, KeyError) as e:
                ai_id = f"<unreadable: {e}>"
        else:
            ai_id = "<missing>"

        root, zip_name = zip_root_dir(addon_dir / "dist", ext_id or name)

        problems = []
        if ext_id is None:
            problems.append("no id in blender_manifest.toml")
        if version is None:
            problems.append("no version in blender_manifest.toml")
        if ext_id != name:
            problems.append(f"manifest id != directory ({ext_id} != {name})")
        if ai_id != name:
            problems.append(f"addon_ai id != directory ({ai_id} != {name})")
        if root is not None and root != name:
            problems.append(f"zip root != directory ({root} != {name}) in {zip_name}")
        if frontend_ids is not None and name not in frontend_ids:
            problems.append("not declared in frontend ADDON_IDS")

        declared_ids.add(name)
        rows.append((
            [name, str(ext_id), str(ai_id), str(root or "—"), str(version)],
            problems,
        ))
        if problems:
            ok = False

    # Size columns to the data. A mismatch is exactly when a value is unexpectedly
    # long, so fixed widths collapse the table right when it needs to be readable.
    headers = ["directory", "manifest.toml", "addon_ai.json", "zip root", "version"]
    widths = [
        max(len(headers[i]), max(len(row[0][i]) for row in rows)) + 2
        for i in range(len(headers))
    ]
    header_line = "".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-" * len(header_line))
    for cells, problems in rows:
        status = "" if not problems else "❌"
        print("".join(c.ljust(w) for c, w in zip(cells, widths)) + status)
        for problem in problems:
            print(f"   ❌ {problem}")

    if frontend_ids is not None:
        orphans = frontend_ids - declared_ids
        if orphans:
            print(f"\n❌ Frontend declares ids with no matching addon: {sorted(orphans)}")
            ok = False

    print()
    if ok:
        print(f"🎉 All {len(addon_dirs)} addon ids agree across manifest, addon_ai.json, "
              f"directory name, packaged zip and the frontend.")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate cr8 addon ids agree everywhere they are written down")
    parser.add_argument(
        "--repo-root", default=None,
        help="Repository root (defaults to this script's parent directory)")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root \
        else Path(__file__).resolve().parent.parent

    print("=== CR8 Addon ID Consistency Check ===\n")
    if not validate(root):
        print("\n❌ Addon ids are inconsistent — see above.")
        sys.exit(1)
    sys.exit(0)
