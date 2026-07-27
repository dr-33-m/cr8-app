#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# cr8-app image builder
#
# Builds any combination of the three deployable images from one
# terminal instead of three:
#
#   blender   backend/cr8_engine/docker  -> cr8-blender  (GPU/Blender runtime)
#   frontend  frontend/                  -> cr8-frontend (TanStack Start)
#   engine    backend/cr8_engine/        -> cr8-engine   (FastAPI)
#
# Usage:
#   ./build.sh frontend                    # build one
#   ./build.sh frontend engine --push      # build several and push
#   ./build.sh all --push                  # the full release
#   ./build.sh all --dry-run               # print the commands, run nothing
#
# Options:
#   --push              Push after building (required for multi-arch)
#   --tag TAG           Image tag (default: latest — pin a real tag for deploys)
#   --registry NS       Registry namespace (default: thamsanqaj)
#   --platform LIST     Platforms for buildx (default: linux/amd64,linux/arm64)
#   --env-file PATH     Frontend build args (default: frontend/.env.release)
#   --no-cache          Pass --no-cache to docker
#   --dry-run           Print commands without executing
#   -h, --help          This message
# ============================================================

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REGISTRY="${CR8_REGISTRY:-thamsanqaj}"
TAG="${CR8_TAG:-latest}"
PLATFORMS="${CR8_PLATFORMS:-linux/amd64,linux/arm64}"
ENV_FILE="$REPO_ROOT/frontend/.env.release"
PUSH=false
DRY_RUN=false
NO_CACHE=""
TARGETS=()

# The frontend bakes VITE_ vars into the bundle at build time, so these must be
# present when the image is built — they cannot be supplied at runtime.
FRONTEND_BUILD_ARGS=(
    VITE_LAUNCH_MODE
    VITE_WEBSOCKET_URL
    VITE_DISCORD_WEBHOOK_URL
    VITE_WEBRTC_SIGNALING_SERVER_URL
    VITE_TURN_SERVER
)

usage() { sed -n '3,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

log()  { echo "==> $*"; }
warn() { echo "WARNING: $*" >&2; }
die()  { echo "ERROR: $*" >&2; exit 1; }

run() {
    if [ "$DRY_RUN" = true ]; then
        printf '  [dry-run]'; printf ' %q' "$@"; printf '\n'
    else
        "$@"
    fi
}

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case $1 in
        blender|frontend|engine) TARGETS+=("$1"); shift ;;
        backend)                 TARGETS+=("engine"); shift ;;   # common alias
        all)                     TARGETS+=(blender frontend engine); shift ;;
        --push)                  PUSH=true; shift ;;
        --tag)                   TAG="${2:?--tag needs a value}"; shift 2 ;;
        --registry)              REGISTRY="${2:?--registry needs a value}"; shift 2 ;;
        --platform)              PLATFORMS="${2:?--platform needs a value}"; shift 2 ;;
        --env-file)              ENV_FILE="${2:?--env-file needs a value}"; shift 2 ;;
        --no-cache)              NO_CACHE="--no-cache"; shift ;;
        --dry-run)               DRY_RUN=true; shift ;;
        -h|--help)               usage; exit 0 ;;
        *) die "Unknown option: $1 (try --help)" ;;
    esac
done

if [ ${#TARGETS[@]} -eq 0 ]; then
    usage
    echo
    die "No targets given. Pick from: blender, frontend, engine, all"
fi

# --tag is the tag only; the image name is built as <registry>/cr8-<target>:<tag>.
# The nested docker/build.sh uses --tag for a *full* image ref, so passing one
# here (old muscle memory) would silently produce
# "thamsanqaj/cr8-blender:thamsanqaj/cr8-blender:latest".
if [[ "$TAG" == */* || "$TAG" == *:* ]]; then
    die "--tag takes just the tag (e.g. 'latest', 'v0.2.0'), not a full image name.
You passed: $TAG
Image names are composed as <registry>/cr8-<target>:<tag>.
For a different namespace use --registry, e.g.:
  ./build.sh blender --registry ${TAG%%/*} --tag ${TAG##*:}"
fi

# De-duplicate while preserving order, so "all frontend" doesn't build twice.
UNIQUE_TARGETS=()
for target in "${TARGETS[@]}"; do
    seen=false
    for existing in ${UNIQUE_TARGETS[@]+"${UNIQUE_TARGETS[@]}"}; do
        [ "$existing" = "$target" ] && seen=true && break
    done
    [ "$seen" = false ] && UNIQUE_TARGETS+=("$target")
done

# Multi-arch images cannot be loaded into the local docker image store — buildx
# can only export them to a registry. Without --push, build for this host only so
# the result is actually usable locally instead of failing at the export step.
if [ "$PUSH" = true ]; then
    OUTPUT_FLAG="--push"
    BUILD_PLATFORMS="$PLATFORMS"
else
    OUTPUT_FLAG="--load"
    BUILD_PLATFORMS=""
    warn "Not pushing — building for this host's architecture only."
    warn "Multi-arch (${PLATFORMS}) requires --push; buildx cannot --load a multi-arch image."
fi

echo
log "cr8-app build"
echo "    targets:   ${UNIQUE_TARGETS[*]}"
echo "    registry:  $REGISTRY"
echo "    tag:       $TAG"
echo "    platforms: ${BUILD_PLATFORMS:-<host>}"
echo "    push:      $PUSH"
[ "$DRY_RUN" = true ] && echo "    dry-run:   yes"
echo

buildx_build() {
    # buildx_build <context-dir> <image> [extra docker args...]
    local context="$1"; shift
    local image="$1"; shift

    local cmd=(docker buildx build)
    [ -n "$BUILD_PLATFORMS" ] && cmd+=(--platform "$BUILD_PLATFORMS")
    [ -n "$NO_CACHE" ] && cmd+=("$NO_CACHE")
    cmd+=("$@")
    cmd+=(-t "$image" -f Dockerfile "$OUTPUT_FLAG" .)

    ( cd "$context" && run "${cmd[@]}" )
}

build_blender() {
    local image="$REGISTRY/cr8-blender:$TAG"
    log "Building $image"

    # Delegated to the existing script: it stages the ~1.2GB Blender build, the
    # gst-plugins-rs binaries and the five addon zips into the build context,
    # then cleans up. Single-arch by nature — the image bundles an x86_64 Blender
    # build on a CUDA base, so --platform would be a lie.
    local args=(--tag "$image")
    [ "$PUSH" = true ] && args+=(--push)
    ( cd "$REPO_ROOT/backend/cr8_engine/docker" && run ./build.sh "${args[@]}" )
}

build_frontend() {
    local image="$REGISTRY/cr8-frontend:$TAG"
    log "Building $image"

    [ -f "$ENV_FILE" ] || die "Frontend build args not found: $ENV_FILE
Copy frontend/.env.release.example to $ENV_FILE and fill in your deploy values.
Do NOT point --env-file at frontend/.env — that is the local-dev config and
would bake localhost URLs into a deployed image."

    # shellcheck disable=SC1090
    set -a; source "$ENV_FILE"; set +a

    local build_args=()
    local missing=()
    for arg in "${FRONTEND_BUILD_ARGS[@]}"; do
        if [ -z "${!arg:-}" ]; then
            missing+=("$arg")
        else
            build_args+=(--build-arg "$arg=${!arg}")
        fi
    done
    [ ${#missing[@]} -gt 0 ] && die "Missing in $ENV_FILE: ${missing[*]}"

    # VITE_ vars are inlined into the bundle at build time, so a local-mode value
    # produces an image that will try to reach localhost from the user's browser.
    # The build would succeed and only fail once deployed — worth stopping for.
    if [ "${VITE_LAUNCH_MODE}" = "local" ] && [ "$PUSH" = true ]; then
        die "VITE_LAUNCH_MODE=local in $ENV_FILE but you asked to --push.
That would publish an image hardcoded to localhost. Set VITE_LAUNCH_MODE=remote
(and remote URLs) in $ENV_FILE, or drop --push to build it locally."
    fi
    if [[ "${VITE_WEBSOCKET_URL}" == *localhost* || "${VITE_WEBSOCKET_URL}" == *127.0.0.1* ]] \
       && [ "$PUSH" = true ]; then
        die "VITE_WEBSOCKET_URL points at localhost ($VITE_WEBSOCKET_URL) but you asked to --push."
    fi

    buildx_build "$REPO_ROOT/frontend" "$image" "${build_args[@]}"
}

build_engine() {
    local image="$REGISTRY/cr8-engine:$TAG"
    log "Building $image"
    # No build args — the engine reads everything from runtime env.
    buildx_build "$REPO_ROOT/backend/cr8_engine" "$image"
}

BUILT=()
for target in "${UNIQUE_TARGETS[@]}"; do
    case "$target" in
        blender)  build_blender ;;
        frontend) build_frontend ;;
        engine)   build_engine ;;
    esac
    BUILT+=("$target")
    echo
done

log "Done: ${BUILT[*]}"
for target in "${BUILT[@]}"; do
    case "$target" in
        blender)  echo "    $REGISTRY/cr8-blender:$TAG" ;;
        frontend) echo "    $REGISTRY/cr8-frontend:$TAG" ;;
        engine)   echo "    $REGISTRY/cr8-engine:$TAG" ;;
    esac
done
[ "$PUSH" = false ] && echo && warn "Nothing was pushed (no --push)."
exit 0
