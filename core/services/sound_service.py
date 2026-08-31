"""
Sound and Volume Service for QuakMeeting.
Handles cross-platform notification chime playback with system volume detection (macOS & Linux).
Ensures sounds are only played when computer volume is on and unmuted.
"""
from __future__ import annotations
import os
import sys
import shutil
import subprocess
import threading
import logging
from typing import Optional

from core.services.config_service import config

logger = logging.getLogger("QuakMeeting.SoundService")


def is_system_volume_on() -> bool:
    """
    Checks if the operating system audio output is unmuted and volume > 0.
    Returns True if audio is enabled/on, False if muted or 0 volume.
    """
    if sys.platform == "darwin":
        try:
            # Check macOS output muted setting
            res_mute = subprocess.run(
                ["osascript", "-e", "output muted of (get volume settings)"],
                capture_output=True, text=True, timeout=1
            )
            if res_mute.returncode == 0 and "true" in res_mute.stdout.lower():
                return False

            # Check macOS output volume (0-100)
            res_vol = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True, text=True, timeout=1
            )
            if res_vol.returncode == 0:
                vol_val = int(res_vol.stdout.strip())
                if vol_val <= 0:
                    return False
            return True
        except Exception as e:
            logger.debug(f"macOS volume detection fallback: {e}")
            return True

    # Linux (PipeWire / PulseAudio / ALSA)
    if shutil.which("wpctl"):
        try:
            res = subprocess.run(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                capture_output=True, text=True, timeout=1
            )
            if res.returncode == 0:
                out = res.stdout.strip()
                if "[MUTED]" in out:
                    return False
                parts = out.split()
                if len(parts) >= 2:
                    try:
                        vol = float(parts[1])
                        if vol <= 0.0:
                            return False
                    except ValueError:
                        pass
                return True
        except Exception:
            pass

    if shutil.which("pactl"):
        try:
            res = subprocess.run(
                ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                capture_output=True, text=True, timeout=1
            )
            if res.returncode == 0 and "yes" in res.stdout.lower():
                return False
        except Exception:
            pass

    if shutil.which("amixer"):
        try:
            res = subprocess.run(
                ["amixer", "get", "Master"],
                capture_output=True, text=True, timeout=1
            )
            if res.returncode == 0:
                if "[off]" in res.stdout:
                    return False
        except Exception:
            pass

def is_in_lesson_now(event_dict: Optional[dict] = None) -> bool:
    """Checks if the user is currently attending an active lecture/lesson."""
    try:
        if event_dict and (event_dict.get("is_test_banner") or "TEST FLIGHT" in str(event_dict.get("action_btn_text", ""))):
            return False
        from core.services.calendar_service import calendar_service
        return calendar_service.is_in_lesson()
    except Exception as e:
        logger.debug(f"Could not check active lesson status: {e}")
        return False


def play_chime(
    sound_name: Optional[str] = None,
    sync: bool = False,
    event_dict: Optional[dict] = None
) -> None:
    """
    Plays notification chime asynchronously (or synchronously if sync=True) if sound is enabled,
    system volume is on, and the user is not currently attending a university lecture/lesson.
    """
    if not config.get("sound_enabled", True):
        return

    if event_dict and event_dict.get("is_quiet_reminder"):
        logger.debug("Quiet reminder; skipping chime.")
        return

    if config.get("mute_during_lessons", True):
        if is_in_lesson_now(event_dict):
            logger.info("Chime muted: user is currently attending a lecture/lesson (mute_during_lessons enabled).")
            return

    def _play_async():
        try:
            if not is_system_volume_on():
                logger.debug("System volume is muted or at 0; skipping chime.")
                return

            snd = sound_name or config.get("sound_name", "Glass")

            if sys.platform == "darwin":
                sound_path = f"/System/Library/Sounds/{snd}.aiff"
                if os.path.exists(sound_path):
                    subprocess.run(["afplay", sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    try:
                        import AppKit
                        nssnd = AppKit.NSSound.soundNamed_(snd)
                        if nssnd:
                            nssnd.play()
                    except Exception:
                        pass
                return

            # Linux Sound Playback
            # 1. libcanberra (Standard freedesktop event sounds)
            if shutil.which("canberra-gtk-play"):
                res = subprocess.run(
                    ["canberra-gtk-play", "-i", "message"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                if res.returncode == 0:
                    return

            # 2. PipeWire pw-play / PulseAudio paplay / ALSA aplay with system sound files
            sound_candidates = [
                "/usr/share/sounds/Yaru/stereo/message.oga",
                "/usr/share/sounds/freedesktop/stereo/message.oga",
                "/usr/share/sounds/freedesktop/stereo/bell.oga",
                "/usr/share/sounds/gnome/default/alerts/glass.ogg",
                "/usr/share/sounds/alsa/Front_Center.wav"
            ]
            chosen_file = None
            for p in sound_candidates:
                if os.path.exists(p):
                    chosen_file = p
                    break

            if chosen_file:
                if shutil.which("pw-play"):
                    subprocess.run(["pw-play", chosen_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                if shutil.which("paplay"):
                    subprocess.run(["paplay", chosen_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                if shutil.which("aplay") and chosen_file.endswith(".wav"):
                    subprocess.run(["aplay", chosen_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return

        except Exception as e:
            logger.debug(f"Error during chime playback: {e}")

    if sync:
        _play_async()
    else:
        threading.Thread(target=_play_async, daemon=True).start()
