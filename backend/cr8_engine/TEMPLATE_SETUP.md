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
| Image Path:Tag | `thamsanqaj/cr8-blender:v0.3.0` |

Set an explicit tag, not `:latest`. **You should not need to edit this field again** —
the engine overrides the image per instance via `VASTAI_BLENDER_IMAGE` (Step 9), so
shipping a new build is an engine env change, not a template change.

### Why not `:latest`, and why the override exists

`latest` is a mutable tag: the name stays put while the digest underneath moves. Every
instance lands on a different third-party machine with its own Docker image cache, so
after you push a new build, a machine that has never seen the image pulls it fresh
while a machine that ran the previous build may serve its cached copy. You get a fleet
running two different versions of Blender and the addons — and since the engine accepts
the *cheapest* offer on each launch (Step 9), you land on a different machine almost
every time. The symptom is a bug that reproduces intermittently with nothing in the
code to explain it.

The obvious fix — bump the tag in this field on every release — has a sting: **VastAI
derives a template's `hash_id` from its content, so editing the template rotates the
hash**, and `VASTAI_TEMPLATE_HASH_ID` would have to be updated in `.env` in lockstep
every time.

So the image is overridden at instance-creation time instead. The engine sends `image`
alongside `template_hash_id` on `PUT /asks/{offer_id}/`; VastAI merges request over
template per-field, so the image wins while this template's **environment variables,
on-start script and launch mode still apply**. The template is never edited and its
hash stays stable.

Keep this field pointed at a real image regardless — it is the fallback used whenever
`VASTAI_BLENDER_IMAGE` is unset.

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
VASTAI_BLENDER_IMAGE=thamsanqaj/cr8-blender:v0.3.0
SSH_PRIVATE_KEY_PATH=~/.ssh/id_rsa
```

`VASTAI_BLENDER_IMAGE` overrides the template's image (see Step 3). Leave it empty to
use whatever the template carries.

That's it. When cr8_engine launches instances, it searches for GPU offers and accepts the cheapest one using this template — the onstart and env config is handled by VastAI, with the image supplied per-request.

## Shipping a new Blender build

The whole release loop, with the template untouched:

```bash
# 1. Build and push with an immutable tag
./build.sh blender --push --tag v0.3.1     # or --tag $(git rev-parse --short HEAD)

# 2. Point the engine at it
#    cr8_engine/.env:  VASTAI_BLENDER_IMAGE=thamsanqaj/cr8-blender:v0.3.1

# 3. Restart the engine — config is read once at startup
```

Instances launched from then on pull the new image. **Already-running instances keep
the old one** — they were created with the tag that was current at accept time, so
either wait for them to be torn down or destroy them deliberately.

Rolling back is the same three steps with the previous tag. That is the payoff for
immutable tags: `latest` would leave you reverting git and rebuilding under pressure.

If you want a guarantee no cache can defeat, pin a digest instead of a tag
(`thamsanqaj/cr8-blender@sha256:...`). Less readable, fully immutable.
