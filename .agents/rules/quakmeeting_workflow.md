---
name: quakmeeting-workflow
description: Architecture rules, Today-only calendar filtering, and the mandatory 4-step development workflow for QuakMeeting.
trigger: always_on
---

# QuakMeeting Rules & Workflow

Refer to [.docs/PROJECT_GUIDE.md](.docs/PROJECT_GUIDE.md) for comprehensive architecture details.

## ⚡ Mandatory 4-Step Development Workflow (Execute on Every Change)
Depending on your current OS environment, execute the correct sequence:

### 🍎 macOS Workflow
1. **Test**: `python3 -m unittest discover -s tests -v`
2. **Build**: `python3 build_macos_app.py`
3. **Restart**: `pkill -f "QuakMeeting" 2>/dev/null; sleep 1; open /Applications/QuakMeeting.app`
4. **Verify**: `sleep 2 && ps aux | grep -i "[Q]uakMeeting" && tail -15 ~/.quakmeeting/quakmeeting.log`

### 🐧 Ubuntu/Linux Workflow
1. **Test**: `python3 -m unittest discover -s tests -v`
2. **Build & Install**: `bash scripts/build_ubuntu_deb.sh && sudo dpkg -i deb_dist/*.deb`
3. **Restart**: `pkill -f "quakmeeting" 2>/dev/null; pkill -f "main.py" 2>/dev/null; sleep 1; quakmeeting &`
4. **Verify**: `sleep 2 && ps aux | grep -i "quakmeeting" && tail -15 ~/.quakmeeting/quakmeeting.log`

## 🛑 Critical Rules
- **No Auto-Commit**: Never commit changes to git automatically. Only commit when the user explicitly asks for a commit.
- **Today-Only Filter**: The calendar service, agenda, and status bar only load and evaluate events for Today (00:00 to 23:59:59).
- **Transit vs Meetings**: Travel events trigger notification stages relative to `departure_time` (leave time). Video/desk meetings trigger relative to `start_time`.
- **Duration Formatting**: Use `format_duration()` for clean hour/minute display (e.g. 120m → 2h, 90m → 1h 30m).
- **In-Process Python Launcher**: Preserve native Mach-O launcher with `dlopen`/`Py_Main` so top menu bar renders properly.
