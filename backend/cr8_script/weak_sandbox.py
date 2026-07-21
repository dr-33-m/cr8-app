# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Vendored from the Blender MCP add-on (blender_mcp 1.0.0). The mechanism is
# unchanged; the blocklist is extended for cr8's hosted-session model — see
# _BLOCKED_OPS below.

"""
Weak sandbox for LLM-generated code execution.

Note that this isn't really a sandbox,
more guidance that some things should not be done.

Notes:

- The reason *not* to use the prompt is that it tends not to be reliable,
  sometimes initial requests leave the context window (or are ignored for whatever reason),
  so we are better off with a simple way to prevent some things from happening.

- If the LLM (or its user) is motivated these can be worked around.
  This is more of a slap on the wrist not to try some things.
"""

__all__ = (
    "WeakSandboxForLLM",
)

import sys
from typing import Any, Self


def _blocked_exit(*args: object, **kwargs: object) -> None:  # noqa: ARG001
    raise RuntimeError("sys.exit() is not allowed in LLM-generated code")


def _blocked_quit(*args: object, **kwargs: object) -> None:  # noqa: ARG001
    raise RuntimeError(
        "bpy.app.quit() is not allowed: it terminates Blender on the user's "
        "cloud instance, ending their session"
    )


def _overrides() -> tuple[tuple[object, str, object], ...]:
    """
    Build the attribute override table.

    Deferred to a function so `bpy` is imported at call time rather than module
    import time (the add-on registry imports this module during discovery).
    Each entry is `(object, attr_name, replacement)`.
    """
    import bpy  # pylint: disable=import-error

    overrides: list[tuple[object, str, object]] = [
        (sys, "exit", _blocked_exit),
    ]

    # Upstream's `wm.quit_blender` message points the LLM at `bpy.app.quit()` as
    # the sanctioned alternative. For a hosted session it is equally fatal, so we
    # would like to close that door too — but the attribute does not exist on
    # every build, and `bpy.app` is a static struct that can reject assignment.
    # Only take it when the build actually offers it; `override_store` tolerates
    # the rest.
    if hasattr(bpy.app, "quit"):
        overrides.append((bpy.app, "quit", _blocked_quit))

    return tuple(overrides)


# Operators that LLM-generated code must not access.
# Each entry is `("module.func", "reason")`.
#
# Use this sparingly.
# The rule of thumb for inclusion is:
#
#    The operator is guaranteed to cause problems and/or failure.
#
# There are lots of operations that are fairly questionable:
# - `bpy.ops.screen.spacedata_cleanup`.
# - `bpy.ops.wm.previews_clear`
#
# but it's not the purpose of this weak sandbox to disallow
# things the LLM probably shouldn't be doing.
#
# The cr8 entries below meet that bar specifically because Blender runs as a
# hosted, cloud-backed session here rather than on the user's desktop.
#
_BLOCKED_OPS: tuple[tuple[str, str], ...] = (
    (
        "wm.quit_blender",
        "Terminates Blender on the user's cloud instance, ending their session "
        "and losing unsaved work",
    ),
    (
        "wm.read_factory_settings",
        "Resets all user preferences, which disables the cr8 add-ons and cuts "
        "the connection to the engine — there is no way to recover mid-session",
    ),
    (
        "wm.read_factory_userpref",
        "Resets all user preferences, which disables the cr8 add-ons and cuts "
        "the connection to the engine",
    ),
    ("wm.read_userpref", "May reset user preferences disabling the cr8 add-ons, avoid calling"),
    # cr8-specific: the .blend is cloud-backed and the engine/frontend track
    # project state, so swapping the open file out from under them desyncs the
    # session and discards the user's work.
    (
        "wm.read_homefile",
        "Discards the user's project. Their .blend is cloud-backed and the "
        "session tracks it — delete objects individually instead",
    ),
    (
        "wm.open_mainfile",
        "Replaces the user's project and desynchronises the session from the "
        "engine's view of it",
    ),
    (
        "wm.save_as_mainfile",
        "Repoints the file path and breaks cloud saving. Use the session's own "
        "save action instead of saving from code",
    ),
)

_BLOCKED_OPS_SET: frozenset[str] = frozenset(op for op, _reason in _BLOCKED_OPS)


class WeakSandboxForLLM:
    """Context manager wrapping ``exec()`` of LLM-generated code."""
    __slots__ = (
        "_store_attrs",
        "_store_ops",
    )

    # -------------------------------------------------------------------------
    # Attribute overrides

    @staticmethod
    def override_store() -> list[tuple[object, str, object]]:
        """
        Save current values listed in the override table and apply replacements.

        Entries that cannot be read or written are skipped rather than raised:
        `bpy` attributes come and go between builds, and several live on static
        structs that reject assignment. This runs in `__enter__`, before any
        agent code, so an exception here would fail *every* execute_python call
        outright — a slightly weaker guard is much the lesser evil.
        """
        saved: list[tuple[object, str, object]] = []
        for obj, attr, replacement in _overrides():
            try:
                original = getattr(obj, attr)
                setattr(obj, attr, replacement)
            except (AttributeError, TypeError) as ex:
                print(
                    "Warning: cr8_script sandbox could not override {!r}: {:s}".format(
                        attr, str(ex),
                    ),
                    file=sys.stderr,
                )
                continue
            saved.append((obj, attr, original))
        return saved

    @staticmethod
    def override_restore(saved: list[tuple[object, str, object]]) -> None:
        """
        Restore values previously captured by :meth:`override_store`.

        Only entries that were successfully overridden are present, but restore
        defensively anyway: leaving a block in place would poison every later
        call in the session.
        """
        for obj, attr, original in saved:
            try:
                setattr(obj, attr, original)
            except (AttributeError, TypeError) as ex:
                print(
                    "Warning: cr8_script sandbox could not restore {!r}: {:s}".format(
                        attr, str(ex),
                    ),
                    file=sys.stderr,
                )

    # -------------------------------------------------------------------------
    # Operator blocking

    @staticmethod
    def ops_blocked_store() -> tuple[Any, Any]:
        """Replace ``bpy.ops._op_create_function`` with a filtered wrapper.

        Returns ``(bpy_ops_module, original_function)`` for later restore, or
        ``(None, None)`` when the hook is unavailable. ``_op_create_function`` is
        private API, so a build may rename or drop it; losing the operator guard
        is acceptable, failing every execute_python call is not.
        """
        import bpy.ops as _bpy_ops  # noqa: WPS433

        original = getattr(_bpy_ops, "_op_create_function", None)
        if original is None:
            print(
                "Warning: cr8_script sandbox could not hook bpy.ops "
                "(_op_create_function missing); operator blocking is inactive",
                file=sys.stderr,
            )
            return (None, None)

        def _filtered_op_create_function(module: str, func: str) -> Any:
            key = "{:s}.{:s}".format(module, func)
            if key in _BLOCKED_OPS_SET:
                reason = next(r for op, r in _BLOCKED_OPS if op == key)

                def _blocked(
                        *args: tuple[object, ...],
                        **kwargs: dict[str, object],
                ) -> None:
                    # Include the arguments as they may help the LLM pin-point the cause of the error.
                    args_str = ", ".join(
                        [repr(a) for a in args] + ["{:s}={!r}".format(k, v) for k, v in kwargs.items()]
                    )
                    raise RuntimeError(
                        "Operator 'bpy.ops.{:s}({:s})' is not allowed in LLM-generated code: {:s}".format(
                            key, args_str, reason,
                        )
                    )

                return _blocked
            return original(module, func)

        _bpy_ops._op_create_function = _filtered_op_create_function
        return (_bpy_ops, original)

    @staticmethod
    def ops_blocked_restore(saved: tuple[Any, Any]) -> None:
        """Restore the original ``_op_create_function``, if it was hooked."""
        bpy_ops_module, original = saved
        if bpy_ops_module is None:
            return
        bpy_ops_module._op_create_function = original

    # -------------------------------------------------------------------------
    # Context manager

    def __enter__(self) -> Self:
        self._store_attrs = self.override_store()
        self._store_ops = self.ops_blocked_store()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        del exc_type, exc_val, exc_tb
        self.ops_blocked_restore(self._store_ops)
        self.override_restore(self._store_attrs)
