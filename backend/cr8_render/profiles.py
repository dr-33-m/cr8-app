"""
Render profiles — every tunable constant for image rendering in one place.

The user picks a camera, a resolution and an engine. Everything that actually
determines quality (sample counts, denoising, bounces, compute device) is chosen
here, because a creative cares about "4K" and not about an adaptive sampling
noise threshold.

Values are the widely-recommended production combination rather than anything
novel: Cycles at 256 max samples with adaptive sampling at a 0.01 noise
threshold and OpenImageDenoise, EEVEE at 128 TAA samples with raytracing on.
Adaptive sampling at 0.01 cuts 20-40% off render time with no visible
difference, and OIDN has run on the GPU for NVIDIA RTX/GTX-16xx since Blender
4.1 — which is every card we rent.
"""

import logging

logger = logging.getLogger(__name__)

# --- Engine identifiers ---------------------------------------------------
# EEVEE's identifier changed in Blender 5.0: it was BLENDER_EEVEE_NEXT in
# 4.2-4.5 and is BLENDER_EEVEE again from 5.0. The image ships 5.1, but resolve
# it against the actual enum at call time rather than hardcoding — a wrong
# identifier fails the render outright, and this is cheap insurance.
EEVEE_CANDIDATES = ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT')
CYCLES = 'CYCLES'

# --- Output ---------------------------------------------------------------
IMAGE_FORMAT = 'PNG'
IMAGE_COLOR_MODE = 'RGBA'
IMAGE_COLOR_DEPTH = '8'
PNG_COMPRESSION = 15

THUMB_LONG_EDGE = 640
THUMB_QUALITY = 85

# --- Resolution tiers (long edge in pixels) -------------------------------
RESOLUTIONS = {
    'hd': 1920,
    '2k': 2560,
    '4k': 3840,
}
DEFAULT_RESOLUTION = 'hd'

# --- Aspect ratios (width, height) ----------------------------------------
ASPECTS = {
    '16:9': (16, 9),
    '9:16': (9, 16),
    '1:1': (1, 1),
    '4:5': (4, 5),
    '3:2': (3, 2),
}
DEFAULT_ASPECT = '16:9'

# --- Per-engine quality profiles ------------------------------------------
# Applied through _set(), which skips properties this Blender doesn't have.
# That tolerance is deliberate: scene.eevee.gtao_distance moved to the view
# layer as ambient_occlusion_distance in 5.0, and a straight-line block of
# assignments would raise on the first property that moved instead of rendering.

CYCLES_PROFILE = {
    'samples': 256,
    'use_adaptive_sampling': True,
    'adaptive_threshold': 0.01,
    'use_denoising': True,
    'denoiser': 'OPENIMAGEDENOISE',
    'denoising_input_passes': 'RGB_ALBEDO_NORMAL',
    'denoising_prefilter': 'ACCURATE',
    'denoising_use_gpu': True,
    'use_auto_tile': True,
    'max_bounces': 12,
}

EEVEE_PROFILE = {
    'taa_render_samples': 128,
    'use_raytracing': True,
    'ray_tracing_method': 'SCREEN',
    'use_shadows': True,
    'shadow_ray_count': 2,
    'shadow_step_count': 6,
    'volumetric_samples': 64,
}

# Safety valve. Cycles stops sampling at the cap and still writes the image, so
# a pathological scene costs a noisier render instead of an hour of blocked main
# thread on a GPU that bills by the hour. 0 disables.
CYCLES_TIME_LIMIT_SECONDS = 600


def _set(obj, name, value):
    """Assign a property if this Blender build has it, else log and move on.

    Returns True if applied. The alternative — plain assignment — turns any
    upstream property rename into a failed render rather than a slightly
    different one.
    """
    if obj is None or not hasattr(obj, name):
        logger.warning(f"Skipping unknown property '{name}' on {type(obj).__name__}")
        return False
    try:
        setattr(obj, name, value)
        return True
    except Exception as e:
        logger.warning(f"Could not set '{name}' = {value!r}: {e}")
        return False


def resolve_engine(scene, engine: str) -> str:
    """Map a UI engine choice onto an identifier this Blender actually offers."""
    if (engine or '').upper() == CYCLES:
        return CYCLES

    try:
        available = {
            item.identifier
            for item in scene.render.bl_rna.properties['engine'].enum_items
        }
    except Exception:
        available = set()

    for candidate in EEVEE_CANDIDATES:
        if candidate in available:
            return candidate

    # Nothing matched — hand back the modern name and let Blender complain
    # with a message more useful than anything invented here.
    logger.warning(f"No known EEVEE identifier in {available or 'unknown enum'}")
    return EEVEE_CANDIDATES[0]


def compute_dimensions(resolution: str, aspect: str) -> tuple:
    """(width, height) for a resolution tier and aspect, long edge = the tier."""
    long_edge = RESOLUTIONS.get((resolution or '').lower(), RESOLUTIONS[DEFAULT_RESOLUTION])
    ratio_w, ratio_h = ASPECTS.get(aspect or '', ASPECTS[DEFAULT_ASPECT])

    if ratio_w >= ratio_h:
        width = long_edge
        height = int(round(long_edge * ratio_h / ratio_w))
    else:
        height = long_edge
        width = int(round(long_edge * ratio_w / ratio_h))
    # Even dimensions keep encoders happy and cost nothing here.
    return width - (width % 2), height - (height % 2)


def configure_cycles_device(cycles_prefs) -> str:
    """Point Cycles at the GPU. Returns the device type actually selected.

    NVIDIA only, so this is OptiX first (hardware RT, materially faster on RTX)
    then CUDA, then CPU. CPU is a real fallback, not a failure: a slow render
    beats a broken one, and it is logged loudly enough to notice.
    """
    if cycles_prefs is None:
        return 'CPU'

    for device_type in ('OPTIX', 'CUDA'):
        try:
            cycles_prefs.compute_device_type = device_type
        except Exception:
            continue  # not compiled into this build

        try:
            devices = cycles_prefs.get_devices_for_type(device_type)
        except Exception as e:
            logger.warning(f"Could not enumerate {device_type} devices: {e}")
            continue

        if not devices:
            continue

        for device in devices:
            device.use = True
        # Leave CPU out: a rented box's vCPUs generally drag the render out
        # rather than shortening it.
        for device in getattr(cycles_prefs, 'devices', []):
            if getattr(device, 'type', None) == 'CPU':
                device.use = False

        logger.info(f"Cycles using {device_type} ({len(devices)} device(s))")
        return device_type

    logger.warning("No OptiX or CUDA device available — Cycles falling back to CPU")
    return 'CPU'


def apply_profile(scene, engine_id: str):
    """Apply the per-engine quality profile to the scene."""
    if engine_id == CYCLES:
        cycles = getattr(scene, 'cycles', None)
        for name, value in CYCLES_PROFILE.items():
            _set(cycles, name, value)
        _set(cycles, 'device', 'GPU')
        if CYCLES_TIME_LIMIT_SECONDS:
            _set(cycles, 'time_limit', CYCLES_TIME_LIMIT_SECONDS)
    else:
        eevee = getattr(scene, 'eevee', None)
        for name, value in EEVEE_PROFILE.items():
            _set(eevee, name, value)


def apply_output_settings(scene):
    """PNG, 8-bit RGBA. Colour management is left exactly as the scene has it —
    the artist's view transform is part of their look, not ours to override."""
    image_settings = scene.render.image_settings
    _set(image_settings, 'file_format', IMAGE_FORMAT)
    _set(image_settings, 'color_mode', IMAGE_COLOR_MODE)
    _set(image_settings, 'color_depth', IMAGE_COLOR_DEPTH)
    _set(image_settings, 'compression', PNG_COMPRESSION)
