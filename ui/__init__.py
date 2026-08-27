"""
QuakMeeting UI Package.

Subpackages:
  - `ui.macos`: Native macOS UI components (PyObjC / AppKit / Quartz 2D).
  - `ui.linux`: Native Linux / Ubuntu UI components (PyQt6 / Wayland / X11).
  - `ui.common`: Shared UI helpers, viewmodels, and banner queues.
"""
from .app_launcher import launch_application

__all__ = [
    "launch_application",
]
