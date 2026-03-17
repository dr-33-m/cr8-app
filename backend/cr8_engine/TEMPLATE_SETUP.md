# VastAI Template Setup

Create a template on VastAI that bundles your Docker image, startup script, and environment variables. Once created, set the template **hash ID** in your `.env` and you're done.

## Step 1: Go to Templates

Open [cloud.vast.ai/templates](https://cloud.vast.ai/templates/) and click **+ New**.

## Step 2: Identification

| Field | Value |
|-------|-------|
| Template Name | `cr8-blender` |
| Description | Headless Blender 5.1 with WebRTC streaming for cr8-app |

## Step 3: Docker Image

| Field | Value |
|-------|-------|
| Image Path:Tag | `thamsanqaj/cr8-blender:latest` |

## Step 4: Launch Mode

Select **SSH** (not Jupyter, not Entrypoint).

This lets cr8_engine SSH into the instance to launch Blender processes per user.

## Step 5: On-start Script

Paste this into the **On-start Script** field:

```bash
/opt/cr8/start-xorg.sh
```

This is lightweight — it just persists environment variables to `/etc/environment` so they're available in SSH sessions.

The heavy lifting (NVIDIA driver download, Xorg startup, Blender launch) is handled on-demand by `/opt/cr8/launch-blender.sh`, which cr8_engine calls via SSH when a user requests a Blender instance. This gives the engine full visibility into each step via structured output.

## Step 6: Environment Variables

Add these in the **Environment Variables** section (`-e` flags):

| Variable | Value | Purpose |
|----------|-------|---------|
| `WS_URL` | `https://engine.cr8.app` | Public URL of your cr8_engine (Blender connects back via WebSocket) |
| `CR8_SIGNALLER_URI` | `wss://signal.cr8.app` | Public URL of your WebRTC signaling server |
| `TURN_SERVER` | `turn://user:pass@turn.cr8.app:3478` | TURN relay server for WebRTC media (required for NAT traversal) |
| `DISPLAY` | `:2` | Headless X display (matches Xorg started in onstart) |

Replace the URLs with your actual deployed VPS addresses.

The TURN server is essential — VastAI instances are behind NAT, so WebRTC media needs a relay. You can self-host one with [coturn](https://github.com/coturn/coturn) on your VPS.

## Step 7: Disk Space

Set disk to **40 GB** (default). The Blender image is ~2.5GB, leaving room for blend files and temp data.

## Step 8: Save

Click **Create** to save the template. Note the **Hash ID** shown on the templates page (a hex string like `4e17788f74f075dd9aab7d0d4427968f`).

You can also retrieve it via the API:
```bash
curl -G "https://console.vast.ai/api/v0/template/" \
  -H "Authorization: Bearer $VAST_API_KEY" \
  --data-urlencode 'select_filters={"name":{"eq":"cr8-blender"}}'
```

## Step 9: Set the Template Hash ID

Add it to your `cr8_engine/.env`:

```env
LAUNCH_MODE=remote
VASTAI_API_KEY=your-api-key-here
VASTAI_TEMPLATE_HASH_ID=your-template-hash-id-here
SSH_PRIVATE_KEY_PATH=~/.ssh/id_rsa
```

That's it. When cr8_engine launches instances, it searches for GPU offers and accepts the cheapest one using this template — all the image, onstart, and env config is handled by VastAI.
