import json
import websocket
import threading
import bpy
import base64
import io
import os
from pathlib import Path
from mathutils import Vector
import tempfile

try:
    import thread
except ImportError:
    import _thread as thread


# Add preview rendering functionality to the existing script
class PreviewRenderer:
    def __init__(self):
        self.preview_dir = Path(tempfile.gettempdir()) / "box_preview"
        self.preview_dir.mkdir(exist_ok=True, parents=True)

    def setup_preview_render(self, params=None):
        # Clear existing node links
        for material in bpy.data.materials:
            if material.use_nodes:
                material.use_nodes = False
                material.use_nodes = True
        # Default or custom render settings
        render = bpy.context.scene.render
        render.engine = 'CYCLES'
        render.image_settings.file_format = 'PNG'

        # Low quality settings for speed
        render.resolution_x = params.get('resolution_x', 480)
        render.resolution_y = params.get('resolution_y', 270)

        bpy.context.scene.cycles.samples = params.get('samples', 16)
        bpy.context.scene.cycles.use_denoising = False

        # Ensure filepath is set for preview frames
        render.filepath = str(self.preview_dir / "frame_")

    def render_preview_frame(self, frame):
        # Ensure scene is set to the correct frame
        bpy.context.scene.frame_set(frame)

        # Specific filepath for this frame
        bpy.context.scene.render.filepath = f"{str(self.preview_dir)}/frame_{frame:04d}.png"

        # Render the frame
        bpy.ops.render.render(write_still=True)

    def cleanup(self):
        # Remove temporary files
        for file in self.preview_dir.glob("frame_*.png"):
            try:
                file.unlink()
            except Exception as e:
                print(f"Error removing file {file}: {e}")


# Initialize preview renderer
preview_renderer = PreviewRenderer()


def create_box(location, size):
    """Create a box with the given parameters"""
    print(f"Creating box at location {location} with size {size}")
    try:
        # Ensure we're in object mode
        if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            enter_editmode=False,
            align='WORLD',
            location=location,
            scale=size
        )
        print("Box created successfully")
        return True
    except Exception as e:
        print(f"Error creating box: {str(e)}")
        return False


def execute_in_main_thread(function, args):
    """Execute a function in Blender's main thread"""
    def wrapper():
        function(*args)
        return None
    bpy.app.timers.register(wrapper, first_interval=0.0)


def on_message(ws, message):
    print(f"\nReceived message from server: {message}")

    try:
        data = json.loads(message)
        print(f"Parsed JSON data: {data}")

        if isinstance(data, dict):
            # Handle existing cube movement
            if all(key in data for key in ['x', 'y', 'z']):
                print("Handling cube movement")

                def update_location():
                    if bpy.data.objects.get("Cube"):
                        obj = bpy.data.objects["Cube"]
                        obj.location.x = float(data['x'])
                        obj.location.y = float(data['y'])
                        obj.location.z = float(data['z'])
                execute_in_main_thread(update_location, ())

            # Handle new box creation command
            elif 'command' in data and data['command'] == 'add_box':
                print("Handling add_box command")
                params = data.get('params', {})
                location = params.get('location', [0, 0, 0])
                size = params.get('size', [1, 1, 1])

                # Convert lists to Vector objects
                loc_vector = Vector(location)
                size_vector = Vector(size)

                print(
                    f"Creating box with params: location={loc_vector}, size={size_vector}")
                execute_in_main_thread(create_box, (loc_vector, size_vector))

              # Add preview rendering command handler
        if data.get('command') == 'start_preview_rendering':
            print("Starting preview rendering")
            params = data.get('params', {})

            def do_preview_render():
                try:
                    # Cleanup any existing preview frames
                    preview_renderer.cleanup()

                    # Setup preview render settings
                    preview_renderer.setup_preview_render(params)

                    # Render multiple frames (e.g., 24 frames)
                    num_frames = params.get('num_frames', 24)
                    for frame in range(1, num_frames + 1):
                        preview_renderer.render_preview_frame(frame)

                        # Send message to trigger frame broadcasting
                    ws.send(json.dumps({
                        "command": "start_broadcast"
                    }))

                except Exception as e:
                    print(f"Preview rendering error: {e}")
                    import traceback
                    traceback.print_exc()

            # Execute rendering in main thread
            execute_in_main_thread(do_preview_render, ())

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()


def on_error(ws, error):
    print(f"WebSocket error: {str(error)}")


def on_close(ws, close_status_code, close_msg):
    print(f"### closed ### status: {close_status_code} msg: {close_msg}")


def on_open(ws):
    print("WebSocket connection opened")

    def run(*args):
        print("Sending initialization message")
        init_message = json.dumps({
            'command': 'initialize',
            'client_type': 'blender'
        })
        ws.send(init_message)
    thread.start_new_thread(run, ())


def on_error(ws, error):
    print(f"WebSocket error: {str(error)}")
    # More detailed error logging


class TestThread(threading.Thread):
    def __init__(self, ctx):
        super(TestThread, self).__init__()
        self.daemon = True

        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("ws://localhost:5001/blender",
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.on_open = on_open
        self.ws = ws

    def run(self):
        self.ws.run_forever()


bl_info = {
    "name": "WebSocket Control",
    "description": "Control Blender via WebSocket",
    "author": "emilie",
    "version": (0, 0, 4),
    "blender": (3, 1, 2),
    "location": "3D View > Tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

# Operator classes


class WSSenderTest(bpy.types.Operator):
    bl_label = "Test Call Server"
    bl_idname = "wm.call_server_hello"

    def execute(self, context):
        print("Calling websocket")
        test_message = json.dumps({
            'command': 'initialize',
            'client_type': 'blender'
        })
        th.ws.send(test_message)
        return {'FINISHED'}


class WSSenderRandom(bpy.types.Operator):
    bl_label = "Move Cube Random"
    bl_idname = "wm.call_server_rand"

    def execute(self, context):
        print("Calling websocket (asking for random values to move the cube)")
        test_message = json.dumps({
            'command': 'generate_random_movement',
            'client_type': 'blender'
        })
        th.ws.send(test_message)
        return {'FINISHED'}


class OBJECT_PT_CustomPanel(bpy.types.Panel):
    bl_label = "Websocket Test"
    bl_idname = "OBJECT_PT_custom_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tools"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.call_server_hello")
        layout.operator("wm.call_server_rand")
        layout.separator()


def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(WSSenderTest.bl_idname)
    self.layout.operator(WSSenderRandom.bl_idname)


def register():
    global th
    ctx = {"lock": threading.Lock()}
    th = TestThread(ctx)
    th.start()

    bpy.utils.register_class(WSSenderTest)
    bpy.utils.register_class(WSSenderRandom)
    bpy.utils.register_class(OBJECT_PT_CustomPanel)
    bpy.types.VIEW3D_MT_object.append(menu_fn)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_fn)
    bpy.utils.unregister_class(WSSenderTest)
    bpy.utils.unregister_class(WSSenderRandom)
    bpy.utils.unregister_class(OBJECT_PT_CustomPanel)
    th.ws.close()
    print('websocket is closed')


if __name__ == "__main__":
    register()
