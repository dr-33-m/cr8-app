# Blender websocket server

`blender_addon_websocket.py` is a Blender add-on to demonstrate that Blender can be made to communicate with a [websocket server](https://websockets.readthedocs.io/en/stable/intro/index.html) (`websocker_server.py`).
This can be useful to make Blender run outside code that might be hard to implement in Blender Python (e.g., because of dependencies), or to simplify porting existing code bases to have a Blender UI.

It is based on this gist: https://gist.github.com/kotobukid/380bf0ac66e128731b95fbccfc583b2b by kotobukid.

## Setup

- Install Python dependencies for the server (this is in system Python):

```
pip install numpy websockets
```

- Install Python dependencies for Blender Python: open Blender python console, and run:

```
import pip
pip.main(['install', 'websocket-client'])
```

- Run Blender from the command line to facilitate debugging. See OS specific instructions: https://docs.blender.org/manual/en/2.79/render/workflows/command_line.html

```
# eg on Mac:
/Applications/Blender.app/Contents/MacOS/Blender
```

- Install the add-on in Blender: `Edit > Preferences > Add-ons > Install...` and choose the file `blender_addon_websocket.py`. Make sure it is enabled with the tick-mark.

## Run

Always start by launching the server first, and then launching Blender, because the add-on expects to open websocket connection upon launch. If it fails to do so, then the connection is broken and Blender must be restarted (or the add-on re-enabled).
The steps go:

- Run the server from system Python:

```
# in command line:
python3 websocker_server.py
```

- Launch Blender from the command line
- Open the `Tools` panel on the right side of the viewport, if it is not visible try pressing `N` to toggle this panel group (includes Item, View, Tools panels).
- Find `Websocket Test` panel
- Click `Test Call Server`: this should show in the server command line that a message is received:

```
Received websocket message.
open ws connection
```

- Click `Move Cube Random`: this should move the default cube by a random vector, each time the button is clicked. If you have no default cube, create one: `Add > Mesh > Cube`. This button is to demonstrate that values can be passed from the Python server to Blender, and be applied on Blender primitives.

## Notes

- After making changes to the add-on code, it must be re-installed. A quick way to edit the add-on is to load it as a file in Blender, edit it there and then `Run` it to re-install it.
- The fact that the client (in Blender) cannot connect to the server except at Blender launch is a bit annoying, I feel like this might be fixable by fixing client code so that there is a way to trigger a websocket connection. The tricky thing is to do so without messing the threads up.
- Currently I used [websockets](https://websockets.readthedocs.io/en/stable/) for the server and [websocket-client](https://websocket-client.readthedocs.io/en/latest/examples.html#creating-your-first-websocket-connection) for the client (in Blender).
