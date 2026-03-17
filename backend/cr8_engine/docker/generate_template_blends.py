"""
Generate startup.blend and userpref.blend for the cr8 application template.

Run during Docker build via:
    blender --background --python generate_template_blends.py

Extensions must already be installed and enabled (via `extension install-file -e`)
before running this script.
"""
import bpy
import os
import shutil

TEMPLATE_DIR = "/opt/blender/5.1/scripts/startup/bl_app_templates_system/cr8"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# --- userpref.blend ---
# Extensions are already enabled from install-file -e calls.
# Save current preferences (which reflect enabled extensions).
bpy.ops.wm.save_userpref()
config_dir = bpy.utils.user_resource('CONFIG')
userpref_src = os.path.join(config_dir, "userpref.blend")
if os.path.exists(userpref_src):
    shutil.copy2(userpref_src, os.path.join(TEMPLATE_DIR, "userpref.blend"))
    print(f"CR8: Copied userpref.blend from {userpref_src}")
else:
    # Fallback: search common locations
    for candidate in [
        os.path.expanduser("~/.config/blender/5.1/config/userpref.blend"),
        "/root/.config/blender/5.1/config/userpref.blend",
    ]:
        if os.path.exists(candidate):
            shutil.copy2(candidate, os.path.join(TEMPLATE_DIR, "userpref.blend"))
            print(f"CR8: Copied userpref.blend from fallback {candidate}")
            break
    else:
        print("CR8: WARNING - Could not find userpref.blend")

# --- startup.blend ---
# Save current scene (factory default) as the template's startup file.
# When Blender opens with --app-template cr8, it loads this instead of
# showing the splash screen.
startup_path = os.path.join(TEMPLATE_DIR, "startup.blend")
bpy.ops.wm.save_as_mainfile(filepath=startup_path)
print(f"CR8: Saved startup.blend to {startup_path}")

print("CR8: Template blend files generated successfully")
