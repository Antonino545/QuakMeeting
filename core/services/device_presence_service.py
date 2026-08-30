"""
Device Presence Service for QuakMeeting.
Runs a lightweight local HTTP server allowing iPhone, iPad, and other devices
to report user activity and study/distraction states via Apple Shortcuts or webhooks.
"""
import http.server
import json
import socket
import threading
import urllib.parse
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from core.domain.models import DeviceActivity, DeviceState, DeviceType
from core.services.config_service import config, ConfigService
from core.services.event_bus import event_bus, EventBus

logger = logging.getLogger("QuakMeeting.DevicePresenceService")


def get_local_ip() -> str:
    """Detects the primary local LAN IP address of this machine (e.g. 192.168.1.42)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an arbitrary public IP (does not actually send packets)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip


def get_local_hostname() -> str:
    """Detects the mDNS / Bonjour .local hostname (e.g. Antoninos-MacBook-Air.local)."""
    import subprocess
    import platform
    if platform.system() == "Darwin":
        try:
            res = subprocess.run(["scutil", "--get", "LocalHostName"], capture_output=True, text=True, timeout=1)
            name = res.stdout.strip()
            if name:
                return f"{name}.local"
        except Exception:
            pass
    try:
        name = socket.gethostname().replace(".local", "")
        return f"{name}.local"
    except Exception:
        return "localhost"


class DeviceRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for device activity pings, status checks, and setup dashboard."""

    server_service: Optional["DevicePresenceService"] = None

    def log_message(self, format: str, *args: Any) -> None:
        """Direct HTTP server logging to QuakMeeting logger instead of stderr."""
        logger.debug(f"[HTTP {self.client_address[0]}] {format % args}")

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 1. Health check
        if path in ("/health", "/api/health"):
            self._respond_json(200, {"status": "healthy", "service": "QuakMeeting Device Presence"})
            return

        # 2. Activity ping via GET (for simple 1-click iOS Shortcuts 'Get Contents of URL')
        if path == "/api/activity":
            self._handle_activity_request(query_params)
            return

        # 3. Status API
        if path == "/api/status":
            self._handle_status_request()
            return

        # 4. Setup & Diagnostic Web Dashboard
        if path in ("", "/setup", "/dashboard"):
            self._handle_setup_page()
            return

        # 5. Interactive Visual AI Diagnostic & Webcam HUD Test Page
        if path in ("/visual-test", "/vision", "/test-vision"):
            self._handle_visual_test_page()
            return

        # 6. Real-time Visual Status API (Lightweight JSON)
        if path in ("/api/visual-status", "/api/vision-status"):
            self._handle_visual_status_api()
            return

        # 7. Live MJPEG Video Stream with Apple Vision HUD Overlay
        if path in ("/video_feed", "/stream", "/api/camera-stream"):
            self._handle_video_feed()
            return

        # 8. Dynamic Apple Shortcut File Generator & Download
        if path in ("/download/shortcut", "/api/shortcut"):
            self._handle_download_shortcut(query_params)
            return

        # Fallback 404
        self._respond_json(404, {"error": "Not Found", "path": path})

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")

        if path == "/api/activity":
            content_length = int(self.headers.get("Content-Length", 0))
            body_data = {}
            if content_length > 0:
                try:
                    raw_body = self.rfile.read(content_length).decode("utf-8")
                    if self.headers.get("Content-Type", "").startswith("application/json"):
                        body_data = json.loads(raw_body)
                    else:
                        parsed_form = urllib.parse.parse_qs(raw_body)
                        body_data = {k: v[0] for k, v in parsed_form.items()}
                except Exception as e:
                    logger.warning(f"Failed to parse POST body: {e}")

            # Merge query params as fallback
            query_params = urllib.parse.parse_qs(parsed_url.query)
            for k, v in query_params.items():
                if k not in body_data and v:
                    body_data[k] = v[0]

            self._handle_activity_request(body_data)
            return

        self._respond_json(404, {"error": "Not Found", "path": path})

    def _handle_activity_request(self, data: Dict[str, Any]) -> None:
        """Processes incoming device activity pings from iPhone, iPad, or Mac."""
        # Unpack params (handling list values from parse_qs or direct values from json)
        def _get_val(key: str, default: str = "") -> str:
            val = data.get(key, default)
            if isinstance(val, list) and val:
                return str(val[0]).strip()
            return str(val).strip() if val is not None else default

        device = _get_val("device") or _get_val("device_type") or "unknown"
        state = _get_val("state") or _get_val("status") or "active"
        app = _get_val("app") or _get_val("app_name") or None
        device_id = _get_val("device_id") or None
        token = _get_val("token")

        # Check authentication token if configured
        expected_token = config.get("device_sync_token", "")
        if expected_token and token != expected_token:
            self._respond_json(401, {"error": "Unauthorized: Invalid or missing security token"})
            return

        activity = DeviceActivity(
            device_type=device,
            state=state,
            device_id=device_id or f"{device}_{self.client_address[0]}",
            app_name=app,
            timestamp=datetime.now(timezone.utc),
            metadata={"client_ip": self.client_address[0]}
        )

        logger.info(f"📱 [DeviceSync] Received ping from {activity.device_type.upper()}: state='{activity.state}', app='{activity.app_name or 'N/A'}' (IP: {self.client_address[0]})")

        # Record activity in service and publish to EventBus
        if self.server_service:
            self.server_service.record_activity(activity)

        self._respond_json(200, {
            "success": True,
            "message": f"Activity recorded for {activity.device_type}",
            "activity": activity.to_dict()
        })

    def _handle_status_request(self) -> None:
        """Returns JSON status of device connections and study state."""
        local_ip = get_local_ip()
        port = config.get("device_sync_port", 8765)

        devices_info = {}
        if self.server_service:
            devices_info = self.server_service.get_devices_status()

        status_data = {
            "status": "online",
            "server_ip": local_ip,
            "port": port,
            "registered_devices": devices_info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._respond_json(200, status_data)

    def _handle_download_shortcut(self, query_params: Dict[str, Any]) -> None:
        """Generates and serves a customized binary Apple .shortcut file for 1-tap import."""
        import plistlib

        def _get_val(key: str, default: str = "") -> str:
            val = query_params.get(key, default)
            if isinstance(val, list) and val:
                return str(val[0]).strip()
            return str(val).strip() if val is not None else default

        device = _get_val("device", "iphone").lower()
        state = "studying" if device == "ipad" else "distracted"
        app_name = "GoodNotes" if device == "ipad" else "Instagram"
        local_host = get_local_hostname()
        port = config.get("device_sync_port", 8765)

        target_url = f"http://{local_host}:{port}/api/activity?device={device}&state={state}&app={app_name}"
        health_url = f"http://{local_host}:{port}/health"

        if device == "iphone":
            actions = [
                {
                    "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
                    "WFWorkflowActionParameters": {
                        "ShowHeaders": False,
                        "WFURL": health_url,
                        "UUID": "HEALTH_CHECK_UUID"
                    }
                },
                {
                    "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
                    "WFWorkflowActionParameters": {
                        "GroupingIdentifier": "COND_GROUP_1",
                        "WFControlFlowMode": 0,
                        "WFCondition": 100,
                        "WFInput": {
                            "Type": "ActionOutput",
                            "OutputUUID": "HEALTH_CHECK_UUID"
                        }
                    }
                },
                {
                    "WFWorkflowActionIdentifier": "is.workflow.actions.delay",
                    "WFWorkflowActionParameters": {
                        "WFDelayTime": 60
                    }
                },
                {
                    "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
                    "WFWorkflowActionParameters": {
                        "ShowHeaders": False,
                        "WFURL": target_url
                    }
                },
                {
                    "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
                    "WFWorkflowActionParameters": {
                        "GroupingIdentifier": "COND_GROUP_1",
                        "WFControlFlowMode": 2
                    }
                }
            ]
        else:
            actions = [
                {
                    "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
                    "WFWorkflowActionParameters": {
                        "ShowHeaders": False,
                        "WFURL": target_url
                    }
                }
            ]

        # Construct Apple Shortcuts property list
        shortcut_dict = {
            "WFWorkflowClientVersion": "2600.0.0",
            "WFWorkflowClientRelease": "2.0",
            "WFWorkflowMinimumClientVersion": 900,
            "WFWorkflowIcon": {
                "WFWorkflowIconGlyphNumber": 59445 if device == "ipad" else 59477,
                "WFWorkflowIconStartColor": 4282601983 if device == "ipad" else 4294924032
            },
            "WFWorkflowImportQuestions": [],
            "WFWorkflowTypes": ["NCWidget", "WatchKit", "QuickActions"],
            "WFWorkflowActions": actions
        }

        try:
            import tempfile
            import os
            import subprocess

            binary_data = plistlib.dumps(shortcut_dict, fmt=plistlib.FMT_BINARY)
            signed_data = binary_data

            # Attempt to sign with macOS native shortcuts CLI for zero iOS Gatekeeper warnings
            try:
                with tempfile.NamedTemporaryFile(suffix=".shortcut", delete=False) as tmp_in, \
                     tempfile.NamedTemporaryFile(suffix=".shortcut", delete=False) as tmp_out:
                    tmp_in.write(binary_data)
                    tmp_in.flush()
                    tmp_in_path = tmp_in.name
                    tmp_out_path = tmp_out.name

                res = subprocess.run(
                    ["shortcuts", "sign", "--mode", "people-who-know-me", "--input", tmp_in_path, "--output", tmp_out_path],
                    capture_output=True,
                    timeout=3
                )
                if res.returncode == 0 and os.path.exists(tmp_out_path) and os.path.getsize(tmp_out_path) > 0:
                    with open(tmp_out_path, "rb") as f:
                        signed_data = f.read()
            except Exception as sign_err:
                logger.debug(f"Shortcut signing skipped/fallback: {sign_err}")
            finally:
                for p in (tmp_in_path, tmp_out_path):
                    if p and os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass

            filename = f"QuakStudy_{device.capitalize()}.shortcut"

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(signed_data)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(signed_data)
            logger.info(f"📲 Generated, signed, and served .shortcut file for {device.upper()} ({len(signed_data)} bytes)")
        except Exception as e:
            logger.error(f"Failed to generate shortcut file: {e}")
            self._respond_json(500, {"error": "Failed to generate shortcut file", "details": str(e)})

    def _handle_video_feed(self) -> None:
        """Streams real-time MJPEG camera frames with Apple Vision neural engine overlay."""
        try:
            import cv2
            import math
            import objc

            # Load Apple Vision framework
            VNDetectFaceRectanglesRequest = None
            VNImageRequestHandler = None
            NSData = None
            try:
                for fw in ["Vision", "CoreGraphics", "CoreImage", "Foundation"]:
                    objc.loadBundle(fw, globals(), bundle_path=f"/System/Library/Frameworks/{fw}.framework")
                VNDetectFaceRectanglesRequest = objc.lookUpClass("VNDetectFaceRectanglesRequest")
                VNImageRequestHandler = objc.lookUpClass("VNImageRequestHandler")
                NSData = objc.lookUpClass("NSData")
            except Exception:
                pass

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self._respond_json(503, {"error": "FaceTime camera unavailable"})
                return

            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self._send_cors_headers()
            self.end_headers()

            from core.domain.models import VisualAttentionState
            from core.services.visual_attention_service import classify_head_pose

            frames_sent = 0
            while frames_sent < 1200: # stream for up to 60s per connection
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.05)
                    continue

                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape

                state = VisualAttentionState.AWAY_NO_FACE
                pitch_val = None
                yaw_val = None
                face_rect = None

                # Process with Apple Vision
                if VNDetectFaceRectanglesRequest and VNImageRequestHandler and NSData:
                    try:
                        _, enc = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                        data_bytes = enc.tobytes()
                        ns_data = NSData.dataWithBytes_length_(data_bytes, len(data_bytes))

                        req = VNDetectFaceRectanglesRequest.alloc().init()
                        try:
                            req.setRevision_(3)
                        except Exception:
                            pass

                        handler = VNImageRequestHandler.alloc().initWithData_options_(ns_data, None)
                        if handler.performRequests_error_([req], None):
                            results = req.results()
                            if results and len(results) > 0:
                                obs = results[0]
                                p = obs.pitch()
                                y = obs.yaw()
                                if p is not None:
                                    pitch_val = float(p)
                                if y is not None:
                                    yaw_val = float(y)

                                bb = obs.boundingBox()
                                bx = int(bb.origin.x * w)
                                by = int((1.0 - (bb.origin.y + bb.size.height)) * h)
                                bw = int(bb.size.width * w)
                                bh = int(bb.size.height * h)
                                face_rect = (bx, by, bw, bh)
                    except Exception:
                        pass

                if pitch_val is not None and yaw_val is not None:
                    state = classify_head_pose(pitch_val, yaw_val)
                elif face_rect is not None:
                    state = VisualAttentionState.FOCUSED_SCREEN

                # Draw bounding box
                if face_rect:
                    bx, by, bw, bh = face_rect
                    box_color = (161, 227, 166) # green
                    if state == VisualAttentionState.FOCUSED_DESK_IPAD:
                        box_color = (250, 180, 137) # blue
                    elif state == VisualAttentionState.DISTRACTED_PHONE:
                        box_color = (168, 139, 243) # red
                    elif state == VisualAttentionState.LOOKING_AWAY:
                        box_color = (175, 226, 249) # yellow

                    cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), box_color, 2)

                # Draw top HUD bar
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, 80), (24, 24, 37), -1)
                cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

                if state == VisualAttentionState.FOCUSED_SCREEN:
                    status_text = "FOCUSED ON MAC SCREEN"
                    status_color = (161, 227, 166)
                elif state == VisualAttentionState.FOCUSED_DESK_IPAD:
                    status_text = "STUDYING ON IPAD / DESK NOTES (SAFE)"
                    status_color = (250, 180, 137)
                elif state == VisualAttentionState.DISTRACTED_PHONE:
                    status_text = "PHONE DISTRACTION DETECTED!"
                    status_color = (168, 139, 243)
                elif state == VisualAttentionState.LOOKING_AWAY:
                    status_text = "LOOKING AWAY"
                    status_color = (175, 226, 249)
                else:
                    status_text = "AWAY / NO FACE DETECTED"
                    status_color = (166, 173, 200)

                p_deg = math.degrees(pitch_val) if pitch_val is not None else 0.0
                y_deg = math.degrees(yaw_val) if yaw_val is not None else 0.0

                cv2.putText(frame, f"State: {status_text}", (15, 36),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                cv2.putText(frame, f"Pitch: {p_deg:+.1f} deg | Yaw: {y_deg:+.1f} deg | Model: Apple Neural Engine", (15, 65),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (166, 173, 200), 1)

                _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_bytes = jpeg.tobytes()

                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(frame_bytes)}\r\n\r\n".encode("utf-8"))
                self.wfile.write(frame_bytes)
                self.wfile.write(b"\r\n")
                frames_sent += 1
                time.sleep(0.04)

            cap.release()
        except Exception as e:
            logger.debug(f"Video feed stream closed: {e}")

    def _handle_visual_status_api(self) -> None:
        """Lightweight JSON API returning instantaneous Apple Vision head pose and attention state in ~5ms."""
        import math
        from core.domain.models import VisualAttentionState
        from core.services.visual_attention_service import visual_attention_service

        try:
            if not visual_attention_service.backend:
                self._respond_json(200, {"state": "away_no_face", "pitch_deg": 0.0, "yaw_deg": 0.0, "state_label": "No backend"})
                return

            state, metrics = visual_attention_service.backend.capture_and_evaluate()
            pitch = metrics.get("pitch", 0.0) if metrics else 0.0
            yaw = metrics.get("yaw", 0.0) if metrics else 0.0

            pitch_deg = math.degrees(pitch)
            yaw_deg = math.degrees(yaw)

            label = "🟢 FOCUSED ON MAC SCREEN"
            color = "#a6e3a1"
            mascot = "🦉"

            if state == VisualAttentionState.FOCUSED_DESK_IPAD:
                label = "📖 STUDYING ON IPAD / DESK NOTES (SAFE)"
                color = "#89b4fa"
                mascot = "🦉"
            elif state == VisualAttentionState.DISTRACTED_PHONE:
                label = "🚨 PHONE DISTRACTION DETECTED!"
                color = "#f38ba8"
                mascot = "🙀"
            elif state == VisualAttentionState.LOOKING_AWAY:
                label = "⚠️ LOOKING AWAY"
                color = "#f9e2af"
                mascot = "🧐"
            elif state == VisualAttentionState.AWAY_NO_FACE:
                label = "☕ AWAY / NO FACE DETECTED"
                color = "#a6adc8"
                mascot = "😴"

            self._respond_json(200, {
                "status": "online",
                "state": state.value,
                "pitch_deg": round(pitch_deg, 1),
                "yaw_deg": round(yaw_deg, 1),
                "state_label": label,
                "badge_color": color,
                "mascot": mascot,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            self._respond_json(500, {"error": str(e)})

    def _handle_visual_test_page(self) -> None:
        """Serves the interactive Visual AI Attention Guardian diagnostic and webcam test page."""
        local_ip = get_local_ip()
        local_host = get_local_hostname()
        port = config.get("device_sync_port", 8765)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 QuakMeeting — Visual AI Attention Guardian Test</title>
    <style>
        :root {{
            --bg-base: #1e1e2e;
            --bg-mantle: #181825;
            --bg-surface: #313244;
            --text-primary: #cdd6f4;
            --text-sub: #a6adc8;
            --accent-green: #a6e3a1;
            --accent-peach: #fab387;
            --accent-blue: #89b4fa;
            --accent-mauve: #cba6f7;
            --accent-red: #f38ba8;
            --accent-yellow: #f9e2af;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-primary);
            padding: 24px;
            display: flex;
            justify-content: center;
        }}
        .container {{ width: 100%; max-width: 760px; }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .header h1 {{ font-size: 26px; color: var(--accent-mauve); margin-bottom: 6px; }}
        .header p {{ color: var(--text-sub); font-size: 14px; }}
        .card {{
            background: var(--bg-mantle);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid var(--bg-surface);
            box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        }}
        .card h2 {{
            font-size: 17px;
            color: var(--accent-blue);
            margin-bottom: 12px;
        }}
        .viewfinder-container {{
            position: relative;
            width: 100%;
            height: 360px;
            background: #11111b;
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid var(--bg-surface);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transform: scaleX(-1);
        }}
        .hud-overlay {{
            position: absolute;
            top: 12px;
            left: 12px;
            right: 12px;
            display: flex;
            justify-content: space-between;
            pointer-events: none;
        }}
        .hud-badge {{
            background: rgba(24, 24, 37, 0.85);
            backdrop-filter: blur(8px);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .state-indicator {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-surface);
            padding: 16px;
            border-radius: 10px;
            margin-top: 16px;
        }}
        .state-title {{ font-size: 13px; color: var(--text-sub); }}
        .state-val {{ font-size: 18px; font-weight: 700; margin-top: 2px; }}
        .mascot-avatar {{ font-size: 42px; }}
        .test-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 14px;
        }}
        .btn {{
            border: none;
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }}
        .btn-green {{ background: var(--accent-green); color: #11111b; }}
        .btn-blue {{ background: var(--accent-blue); color: #11111b; }}
        .btn-red {{ background: var(--accent-red); color: #11111b; }}
        .btn-mauve {{ background: var(--accent-mauve); color: #11111b; }}
        .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
        #toast {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--accent-green);
            color: #11111b;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            display: none;
            z-index: 100;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Visual AI Attention Guardian</h1>
            <p>Live Apple Neural Engine Face & Attention Diagnostics</p>
        </div>

        <div class="card">
            <h2>📷 Live 60 FPS Camera Feed & HUD</h2>
            <div class="viewfinder-container">
                <video id="webcam" autoplay playsinline muted></video>
                <div class="hud-overlay">
                    <div class="hud-badge">⚡ Engine: Apple Vision</div>
                    <div class="hud-badge" id="hudStateBadge" style="color: var(--accent-green);">🟢 ACTIVE</div>
                </div>
            </div>

            <div class="state-indicator">
                <div>
                    <div class="state-title">Live Attention Classification (Apple Neural Engine)</div>
                    <div class="state-val" id="stateLabel" style="color: var(--accent-green);">🟢 FOCUSED ON MAC SCREEN</div>
                    <div style="font-size: 13px; color: var(--text-sub); margin-top: 4px;" id="angleDetails">
                        Pitch: -9.5° | Yaw: -2.1°
                    </div>
                </div>
                <div class="mascot-avatar" id="mascotIcon">🦉</div>
            </div>
        </div>

        <div class="card">
            <h2>🧪 Live Posture Simulator & Banner Test</h2>
            <p style="font-size: 13px; color: var(--text-sub); margin-bottom: 12px;">
                Test how the classifier and mascot respond to different study postures:
            </p>
            <div class="test-grid">
                <button class="btn btn-green" onclick="simulateState('focused_screen', 0, 0, '🟢 Focused on Screen', '🦉')">
                    💻 Screen Focus (0°)
                </button>
                <button class="btn btn-blue" onclick="simulateState('focused_desk_ipad', -28, 5, '📖 iPad / Desk Study Focus', '🦉')">
                    📖 iPad / Desk Study (-28°)
                </button>
                <button class="btn btn-red" onclick="simulateState('distracted_phone', -58, 0, '🚨 Phone Distraction Detected', '🙀')">
                    🚨 Phone Distraction (-58°)
                </button>
                <button class="btn btn-mauve" onclick="triggerLiveAlert()">
                    🔔 Trigger Live Mac Banner
                </button>
            </div>
            <div id="simLog" style="margin-top: 14px; font-size: 13px; color: var(--text-sub);"></div>
        </div>

        <div style="text-align: center; margin-top: 16px;">
            <a href="/" style="color: var(--accent-blue); font-size: 14px; text-decoration: none;">← Back to Device Sync Setup Dashboard</a>
        </div>
    </div>

    <div id="toast">✅ Action Complete!</div>

    <script>
        // Start 60 FPS hardware webcam directly in browser
        navigator.mediaDevices.getUserMedia({{ video: true }})
            .then(stream => {{
                document.getElementById('webcam').srcObject = stream;
            }})
            .catch(err => {{
                console.log("Local camera error:", err);
            }});

        // Poll Apple Neural Engine metrics in real-time
        let isSimulating = false;
        setInterval(() => {{
            if (isSimulating) return;
            fetch('/api/visual-status')
                .then(r => r.json())
                .then(data => {{
                    if (data && data.state_label) {{
                        document.getElementById('stateLabel').innerText = data.state_label;
                        document.getElementById('stateLabel').style.color = data.badge_color;
                        document.getElementById('hudStateBadge').innerText = data.state.toUpperCase();
                        document.getElementById('hudStateBadge').style.color = data.badge_color;
                        document.getElementById('angleDetails').innerText = `Pitch: ${{data.pitch_deg}}° | Yaw: ${{data.yaw_deg}}°`;
                        document.getElementById('mascotIcon').innerText = data.mascot;
                    }}
                }})
                .catch(err => {{}});
        }}, 600);

        function showToast(msg, bg = 'var(--accent-green)', text = '#11111b') {{
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.background = bg;
            t.style.color = text;
            t.style.display = 'block';
            setTimeout(() => {{ t.style.display = 'none'; }}, 2500);
        }}

        function simulateState(stateKey, pitch, yaw, title, mascot) {{
            isSimulating = true;
            document.getElementById('stateLabel').innerText = title;
            document.getElementById('mascotIcon').innerText = mascot;
            document.getElementById('angleDetails').innerText = `Pitch: ${{pitch}}° | Yaw: ${{yaw}}°`;

            let color = 'var(--accent-green)';
            if (stateKey === 'focused_desk_ipad') color = 'var(--accent-blue)';
            if (stateKey === 'distracted_phone') color = 'var(--accent-red)';
            if (stateKey === 'looking_away') color = 'var(--accent-yellow)';

            document.getElementById('stateLabel').style.color = color;
            document.getElementById('hudStateBadge').style.color = color;
            document.getElementById('hudStateBadge').innerText = title.toUpperCase();

            document.getElementById('simLog').innerHTML = `Simulated <strong>${{title}}</strong> (Pitch: ${{pitch}}°). Resuming live AI tracking in 5s...`;
            showToast(`Simulated: ${{title}}`);
            setTimeout(() => {{ isSimulating = false; }}, 5000);
        }}

        function triggerLiveAlert() {{
            fetch('/api/activity?device=iphone&state=distracted&app=Instagram')
                .then(r => r.json())
                .then(data => {{
                    showToast("🚨 Triggered Live Mascot Banner on Mac!", 'var(--accent-red)', '#ffffff');
                    document.getElementById('simLog').innerHTML = `<strong>Live Banner Triggered!</strong> Look at the top right of your Mac screen.`;
                }})
                .catch(err => {{
                    showToast("Error triggering alert", 'var(--accent-red)');
                }});
        }}
    </script>
</body>
</html>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _handle_setup_page(self) -> None:
        """Serves the interactive HTML setup & test page."""
        local_ip = get_local_ip()
        local_host = get_local_hostname()
        port = config.get("device_sync_port", 8765)
        base_url = f"http://{local_host}:{port}"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦆 QuakMeeting — Device Sync & Shortcuts Setup</title>
    <style>
        :root {{
            --bg-base: #1e1e2e;
            --bg-mantle: #181825;
            --bg-surface: #313244;
            --text-primary: #cdd6f4;
            --text-sub: #a6adc8;
            --accent-green: #a6e3a1;
            --accent-peach: #fab387;
            --accent-blue: #89b4fa;
            --accent-mauve: #cba6f7;
            --accent-red: #f38ba8;
            --card-radius: 12px;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-primary);
            margin: 0;
            padding: 24px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 780px;
            width: 100%;
        }}
        .header {{
            text-align: center;
            margin-bottom: 28px;
        }}
        .header h1 {{
            font-size: 28px;
            margin: 0 0 8px 0;
            color: var(--accent-peach);
        }}
        .header p {{
            color: var(--text-sub);
            font-size: 15px;
            margin: 0;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            background: rgba(166, 227, 161, 0.15);
            color: var(--accent-green);
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            margin-top: 12px;
        }}
        .card {{
            background: var(--bg-mantle);
            border: 1px solid var(--bg-surface);
            border-radius: var(--card-radius);
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }}
        .card h2 {{
            margin-top: 0;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .card p {{
            color: var(--text-sub);
            font-size: 14px;
            line-height: 1.5;
        }}
        .code-box {{
            background: var(--bg-base);
            border: 1px solid var(--bg-surface);
            border-radius: 8px;
            padding: 12px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 13px;
            color: var(--accent-blue);
            word-break: break-all;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin: 10px 0;
        }}
        .btn {{
            background: var(--accent-blue);
            color: #11111b;
            border: none;
            padding: 8px 14px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: opacity 0.15s;
        }}
        .btn:hover {{
            opacity: 0.9;
        }}
        .btn-green {{
            background: var(--accent-green);
        }}
        .btn-red {{
            background: var(--accent-red);
        }}
        .test-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 12px;
        }}
        .test-btn {{
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--bg-surface);
            background: var(--bg-surface);
            color: var(--text-primary);
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s;
        }}
        .test-btn:hover {{
            background: rgba(137, 180, 250, 0.2);
            border-color: var(--accent-blue);
        }}
        #toast {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--accent-green);
            color: #11111b;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: none;
            z-index: 100;
        }}
        ol {{
            padding-left: 20px;
            color: var(--text-sub);
            font-size: 14px;
            line-height: 1.6;
        }}
        ol li strong {{
            color: var(--text-primary);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦆 QuakMeeting Device Sync</h1>
            <p>Connect your iPhone & iPad to QuakMeeting on Mac</p>
            <div class="badge">🟢 Server Active: {local_ip}:{port}</div>
        </div>

        <div class="card">
            <h2>🧪 Live Device Simulation & Testing</h2>
            <p>Click these buttons from any browser on your Wi-Fi to test the connection immediately:</p>
            <div class="test-grid">
                <button class="test-btn" onclick="sendPing('ipad', 'studying', 'GoodNotes')">
                    📖 Simulate iPad Study Heartbeat
                </button>
                <button class="test-btn" onclick="sendPing('iphone', 'distracted', 'TikTok')">
                    🚨 Simulate iPhone Distraction
                </button>
            </div>
            <div id="liveStatus" style="margin-top: 14px; font-size: 13px; color: var(--text-sub);"></div>
        </div>

        <div class="card">
            <h2>📱 1. Setup iPad (Active Studying Heartbeat)</h2>
            <p>Automatically inform QuakMeeting when you open your study apps (e.g. GoodNotes, Notability, Books):</p>
            <div style="margin: 14px 0;">
                <a href="/download/shortcut?device=ipad" class="btn btn-green" style="display:inline-block; text-decoration:none; padding:10px 18px; font-size:14px;">
                    📲 1-Tap Download Shortcut for iPad
                </a>
            </div>
            <p style="font-size: 13px; color: var(--text-sub);">Or copy the URL manually:</p>
            <div class="code-box">
                <span id="urlIpad">{base_url}/api/activity?device=ipad&state=studying&app=GoodNotes</span>
                <button class="btn btn-green" onclick="copyText('urlIpad')">Copy URL</button>
            </div>
        </div>

        <div class="card">
            <h2>📱 2. Setup iPhone (Distraction Alert)</h2>
            <p>Trigger a friendly Owl Pilot HUD reminder on Mac when opening distracting apps during study blocks:</p>
            <div style="margin: 14px 0;">
                <a href="/download/shortcut?device=iphone" class="btn btn-red" style="display:inline-block; text-decoration:none; padding:10px 18px; font-size:14px;">
                    📲 1-Tap Download Shortcut for iPhone
                </a>
            </div>
            <p style="font-size: 13px; color: var(--text-sub);">Or copy the URL manually:</p>
            <div class="code-box">
                <span id="urlIphone">{base_url}/api/activity?device=iphone&state=distracted&app=Instagram</span>
                <button class="btn btn-red" onclick="copyText('urlIphone')">Copy URL</button>
            </div>
        </div>
    </div>

    <div id="toast">✅ Ping Sent Successfully!</div>

    <script>
        function copyText(id) {{
            const text = document.getElementById(id).innerText;
            navigator.clipboard.writeText(text).then(() => {{
                showToast("📋 URL Copied to Clipboard!");
            }});
        }}

        function showToast(msg) {{
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => {{ t.style.display = 'none'; }}, 2500);
        }}

        function sendPing(device, state, app) {{
            const url = `/api/activity?device=${{device}}&state=${{state}}&app=${{app}}`;
            fetch(url)
                .then(r => r.json())
                .then(data => {{
                    showToast(`✅ ${{device.toUpperCase()}} (${{state}}): Recorded!`);
                    document.getElementById('liveStatus').innerHTML = `Last activity: <strong>${{device}}</strong> (${{state}}) recorded at ${{new Date().toLocaleTimeString()}}`;
                }})
                .catch(err => {{
                    showToast("❌ Error sending ping: " + err);
                }});
        }}
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _respond_json(self, status_code: int, data: Dict[str, Any]) -> None:
        resp_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(resp_bytes)


class DevicePresenceService:
    """Manages the local HTTP daemon, tracks connected device heartbeats, and broadcasts events."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DevicePresenceService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.config = config
        self.bus = event_bus
        self.server: Optional[http.server.ThreadingHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.registered_devices: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start(self, port: Optional[int] = None) -> bool:
        """Starts the local HTTP listening server in a background daemon thread."""
        if self.is_running:
            logger.debug("DevicePresenceService is already running.")
            return True

        if not self.config.get("device_sync_enabled", True):
            logger.info("DevicePresenceService is disabled in configuration.")
            return False

        server_port = port or int(self.config.get("device_sync_port", 8765))

        # Attach reference to handler
        DeviceRequestHandler.server_service = self

        try:
            # Bind to 0.0.0.0 to accept connections across local Wi-Fi from iPhone & iPad
            self.server = http.server.ThreadingHTTPServer(("0.0.0.0", server_port), DeviceRequestHandler)
            self.is_running = True

            self.server_thread = threading.Thread(
                target=self._run_server_loop,
                name="QuakMeeting-DevicePresenceServer",
                daemon=True
            )
            self.server_thread.start()

            local_ip = get_local_ip()
            logger.info(f"🌐 [DeviceSync] Server running at http://{local_ip}:{server_port}/ (Setup page available)")
            return True
        except Exception as e:
            logger.error(f"Failed to start DevicePresenceService on port {server_port}: {e}")
            self.is_running = False
            return False

    def _run_server_loop(self) -> None:
        """Internal server loop."""
        try:
            if self.server:
                self.server.serve_forever()
        except Exception as e:
            if self.is_running:
                logger.error(f"DevicePresenceService error: {e}")
        finally:
            self.is_running = False

    def stop(self) -> None:
        """Stops the local HTTP server."""
        if not self.is_running or not self.server:
            return
        logger.info("Stopping DevicePresenceService...")
        self.is_running = False
        try:
            self.server.shutdown()
            self.server.server_close()
        except Exception as e:
            logger.warning(f"Error while shutting down DevicePresenceService: {e}")
        self.server = None
        self.server_thread = None

    def record_activity(self, activity: DeviceActivity) -> None:
        """Stores device activity state and dispatches event to EventBus."""
        with self._lock:
            dev_key = activity.device_type.lower()
            self.registered_devices[dev_key] = {
                "device_type": activity.device_type,
                "state": activity.state,
                "app_name": activity.app_name,
                "last_seen": activity.timestamp or datetime.now(timezone.utc),
                "device_id": activity.device_id,
                "metadata": activity.metadata or {}
            }

        # Publish event for StudyFocusGuardian and UI
        self.bus.publish(
            "DEVICE_ACTIVITY_RECEIVED",
            activity=activity,
            device_type=activity.device_type,
            state=activity.state,
            app_name=activity.app_name,
            timestamp=activity.timestamp
        )

    def get_devices_status(self) -> Dict[str, Any]:
        """Returns snapshot of current device states."""
        with self._lock:
            result = {}
            for k, v in self.registered_devices.items():
                res_copy = dict(v)
                if isinstance(res_copy.get("last_seen"), datetime):
                    res_copy["last_seen"] = res_copy["last_seen"].isoformat()
                result[k] = res_copy
            return result

    def get_device_state(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Returns the most recent state record for a specific device type."""
        with self._lock:
            val = self.registered_devices.get(device_type.lower())
            return dict(val) if val else None


# Global singleton instance
device_presence_service = DevicePresenceService()
