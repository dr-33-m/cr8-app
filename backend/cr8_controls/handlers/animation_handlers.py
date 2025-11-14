"""
Animation Control Handlers
Handles all animation-related commands for the Blender Controls addon
"""

import bpy
import logging

logger = logging.getLogger(__name__)


def handle_frame_jump_start() -> dict:
    """Jump to animation start frame"""
    try:
        bpy.ops.screen.frame_jump(end=False)
        current_frame = bpy.context.scene.frame_current
        return {
            "status": "success",
            "message": f"Jumped to start frame ({current_frame})",
            "data": {"current_frame": current_frame}
        }
    except Exception as e:
        logger.error(f"Error jumping to start frame: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to jump to start frame: {str(e)}",
            "error_code": "FRAME_JUMP_ERROR"
        }


def handle_frame_jump_end() -> dict:
    """Jump to animation end frame"""
    try:
        bpy.ops.screen.frame_jump(end=True)
        current_frame = bpy.context.scene.frame_current
        return {
            "status": "success",
            "message": f"Jumped to end frame ({current_frame})",
            "data": {"current_frame": current_frame}
        }
    except Exception as e:
        logger.error(f"Error jumping to end frame: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to jump to end frame: {str(e)}",
            "error_code": "FRAME_JUMP_ERROR"
        }


def handle_keyframe_jump_prev() -> dict:
    """Jump to previous keyframe"""
    try:
        bpy.ops.screen.keyframe_jump(next=False)
        current_frame = bpy.context.scene.frame_current
        return {
            "status": "success",
            "message": f"Jumped to previous keyframe ({current_frame})",
            "data": {"current_frame": current_frame}
        }
    except Exception as e:
        logger.error(f"Error jumping to previous keyframe: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to jump to previous keyframe: {str(e)}",
            "error_code": "KEYFRAME_JUMP_ERROR"
        }


def handle_keyframe_jump_next() -> dict:
    """Jump to next keyframe"""
    try:
        bpy.ops.screen.keyframe_jump(next=True)
        current_frame = bpy.context.scene.frame_current
        return {
            "status": "success",
            "message": f"Jumped to next keyframe ({current_frame})",
            "data": {"current_frame": current_frame}
        }
    except Exception as e:
        logger.error(f"Error jumping to next keyframe: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to jump to next keyframe: {str(e)}",
            "error_code": "KEYFRAME_JUMP_ERROR"
        }


def handle_animation_play() -> dict:
    """Play animation forward"""
    try:
        bpy.ops.screen.animation_play()
        return {
            "status": "success",
            "message": "Animation playing forward",
            "data": {"animation_state": "playing"}
        }
    except Exception as e:
        logger.error(f"Error playing animation: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to play animation: {str(e)}",
            "error_code": "ANIMATION_PLAY_ERROR"
        }


def handle_animation_play_reverse() -> dict:
    """Play animation in reverse"""
    try:
        bpy.ops.screen.animation_play(reverse=True)
        return {
            "status": "success",
            "message": "Animation playing in reverse",
            "data": {"animation_state": "playing_reverse"}
        }
    except Exception as e:
        logger.error(f"Error playing animation in reverse: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to play animation in reverse: {str(e)}",
            "error_code": "ANIMATION_PLAY_ERROR"
        }


def handle_animation_pause() -> dict:
    """Pause animation"""
    try:
        bpy.ops.screen.animation_cancel(restore_frame=False)
        return {
            "status": "success",
            "message": "Animation paused",
            "data": {"animation_state": "paused"}
        }
    except Exception as e:
        logger.error(f"Error pausing animation: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pause animation: {str(e)}",
            "error_code": "ANIMATION_PAUSE_ERROR"
        }
