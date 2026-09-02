---
name: quakmeeting-workflow
description: Required operating guide for all work in QuakMeeting: architecture boundaries, reminder safety rules, verification, and delivery hygiene.
trigger: always_on
---

# QuakMeeting Agent Operating Guide

Read this file before changing the project. For deeper reference, use [docs/PROJECT_GUIDE.md](../../docs/PROJECT_GUIDE.md), [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md), and [docs/CONFIGURATION.md](../../docs/CONFIGURATION.md).

## First actions

1. Verify you are on the `test` branch (`git branch --show-current`) before starting any work. Always ensure you are on `test` before doing anything.
2. Inspect `git status --short`. The worktree may contain user changes; preserve them and do not revert, overwrite, or commit them. and do the pull before starting any work. Always ensure you are on `test` before doing anything.
3. Locate the behavior with `rg` before editing. Read the relevant test and the caller/callee around the change.
4. Keep changes narrow. Add or update regression tests for behavior changes. If making any architectural, structural, or config changes, update the relevant documentation in `docs/` (`docs/ARCHITECTURE.md`, `docs/PROJECT_GUIDE.md`, `docs/CONFIGURATION.md`) before committing.
5. Do not commit, create a branch, alter user calendar/config data, install system dependencies, or publish/release anything unless the user explicitly asks. When committing upon explicit user request, always run and verify that all tests pass before committing. Never commit broken code.

## Architecture boundaries

- `core/domain/` contains data types and pure domain logic. Keep it independent of AppKit, Qt, and provider APIs.
- `core/providers/` fetch calendar data. `core/services/` owns caching, ETA, reminder evaluation, persistence, and the event bus.
- `ui/macos/` is PyObjC/AppKit/Quartz only; `ui/linux/` is PyQt6/AppIndicator only. Put shared presentation logic in `ui/common/`.
- **Cross-Platform UI Parity Invariant**: Whenever UI features, components, layout designs, preferences tabs, or visual styles are modified on macOS (`ui/macos/`), replicate the equivalent design, layout hierarchy, and features on Ubuntu/Linux (`ui/linux/`), and vice-versa. Both desktop platforms must maintain visual styling and functional parity (Catppuccin Mocha theme, cards, controls, action buttons, and status indicators).
- Use `EventBus` to communicate from services to UI. Do not update UI from the background controller directly.
- UI handlers must accept the full published payload, including `event_dict`; event publishers and subscribers must stay compatible.

## Calendar and reminder invariants

- Calendar fetch, agenda, status display, and reminder evaluation are **today-only** in the user's local timezone. Do not surface tomorrow's event early.
- Use `Meeting` and `Meeting.to_dict()` / `Meeting.from_dict()` at service/UI boundaries. Do not invent a second event shape.
- For normal, video, class, food, and general events, reminder stages use `start_time`.
- For travel events with `departure_time`, reminder stages use `departure_time`; an additional start-time reminder may still be emitted by the reminder engine.
- Startup catch-up emits at most one banner for today's most recent due, previously unshown event. Travel events are due at departure; other events are due at start. Never catch up all-day or arrived events.
- Start UI event subscriptions before starting `AppController`; otherwise an event can be recorded as notified before a banner is deliverable.
- Persisted notification state prevents duplicates. Preserve state-key compatibility when changing notification behavior, rescheduling logic, snooze, or arrival suppression.
- Always use `format_duration()` for user-visible durations.

## macOS-specific constraints

- Preserve the in-process Mach-O launcher in `build_macos_app.py`. Replacing it with `execv` or a shell launcher breaks bundle association and the native menu bar.
- Banner overlays must remain on the AppKit main thread. Maintain the non-activating, all-spaces, full-screen auxiliary panel behavior in the banner controller.
- The normal Python path is `/opt/miniconda3/bin/python3`.

## Required verification after code or configuration changes

Run the complete platform workflow. If a command needs system-level permissions, explain the exact action and request approval rather than bypassing it.

### macOS

```bash
# 1. Tests
/opt/miniconda3/bin/python3 -m unittest discover -s tests -v

# 2. Rebuild the bundle
/opt/miniconda3/bin/python3 build_macos_app.py

# 3. Install the fresh bundle, then restart it
ditto "$PWD/QuakMeeting.app" /Applications/QuakMeeting.app
pkill -f "QuakMeeting" 2>/dev/null; sleep 1; open /Applications/QuakMeeting.app

# 4. Confirm process and logs
sleep 2 && ps aux | grep -i "[Q]uakMeeting" && tail -15 ~/.quakmeeting/quakmeeting.log
```

### Ubuntu/Debian Linux

```bash
# 1. Tests
python3 -m unittest discover -s tests -v

# 2. Build the package
bash scripts/build_ubuntu_deb.sh

# 3. Install and restart (requires explicit user approval)
sudo apt-get install --reinstall ./deb_dist/quakmeeting_*_amd64.deb
pkill -f "quakmeeting" 2>/dev/null; sleep 1; quakmeeting &

# 4. Confirm logs
tail -15 ~/.quakmeeting/quakmeeting.log
```

## Delivery checklist

- Before committing changes upon user request, verify that all unit tests pass (`/opt/miniconda3/bin/python3 -m unittest discover -s tests -v`).
- Update documentation in `docs/` (`docs/ARCHITECTURE.md`, `docs/PROJECT_GUIDE.md`, `docs/CONFIGURATION.md`) before committing if any architectural, interface, or configuration changes were made.
- Report the outcome first, then concise evidence: tests/build/restart status and relevant files.
- Call out any verification limitation rather than claiming an unobserved UI result.
- Do not include unrelated existing modifications in the claimed change set.
