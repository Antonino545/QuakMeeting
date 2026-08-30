#!/usr/bin/env python3
"""
Interactive Visual AI Focus & Distraction Guardian Demo for macOS & Linux.
Uses OpenCV for camera display and Apple Vision (Neural Engine) on macOS for real-time 3D Head Pose tracking.
Displays live HUD overlay and triggers Owl Mascot Distraction Banner on distraction.
"""
import sys
import os
import time
import math
from datetime import datetime, timezone, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

# Load native macOS Vision frameworks via PyObjC
VNDetectFaceRectanglesRequest = None
VNImageRequestHandler = None
NSData = None

try:
    import objc
    for fw in ["Vision", "CoreGraphics", "CoreImage", "Foundation"]:
        objc.loadBundle(fw, globals(), bundle_path=f"/System/Library/Frameworks/{fw}.framework")
    VNDetectFaceRectanglesRequest = objc.lookUpClass("VNDetectFaceRectanglesRequest")
    VNImageRequestHandler = objc.lookUpClass("VNImageRequestHandler")
    NSData = objc.lookUpClass("NSData")
    print("✅ Apple Vision Framework loaded via Neural Engine.")
except Exception as e:
    print(f"⚠️ PyObjC Vision fallback mode: {e}")

from core.domain.models import VisualAttentionState, Meeting
from core.services.visual_attention_service import classify_head_pose
from core.services.study_focus_guardian import study_focus_guardian
from core.services.event_bus import event_bus


def main():
    print("=" * 60)
    print("🧠 QuakMeeting — Visual AI Attention Guardian Live Window")
    print("=" * 60)
    print("Opening camera window... (Press 'q' or 'ESC' to quit)")

    # Register simulated active study session
    now = datetime.now(timezone.utc)
    study_m = Meeting(
        title="Studiare Sistemi Operativi",
        start_time=now - timedelta(minutes=5),
        end_time=now + timedelta(hours=2),
        event_type="study",
        pilot_type="owl"
    )
    study_focus_guardian.cached_meetings = [study_m]

    def _on_reminder(meeting=None, stage=None, event_dict=None, **kwargs):
        payload = event_dict or (meeting.to_dict() if meeting else {})
        print(f"\n🚨 [TRIGGERED] OWL MASCOT BANNER: {payload.get('title')}")

    event_bus.subscribe("REMINDER_TRIGGERED", _on_reminder)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Cannot open FaceTime camera. Please check camera permission in System Settings.")
        return

    consecutive_distracted = 0
    last_banner_time = 0

    cv2.namedWindow("QuakMeeting Visual Attention Guardian", cv2.WINDOW_AUTOSIZE)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.03)
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        state = VisualAttentionState.AWAY_NO_FACE
        pitch_val = None
        yaw_val = None
        face_rect = None

        # Process with native Apple Vision Framework
        if VNDetectFaceRectanglesRequest and VNImageRequestHandler and NSData:
            try:
                _, enc = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
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
                        
                        # Pitch / Yaw / Roll from Apple Vision
                        p = obs.pitch()
                        y = obs.yaw()
                        
                        if p is not None:
                            pitch_val = float(p)
                        if y is not None:
                            yaw_val = float(y)

                        # Bounding box (normalized 0-1, bottom-left origin in Vision)
                        bb = obs.boundingBox()
                        bx = int(bb.origin.x * w)
                        by = int((1.0 - (bb.origin.y + bb.size.height)) * h)
                        bw = int(bb.size.width * w)
                        bh = int(bb.size.height * h)
                        face_rect = (bx, by, bw, bh)
            except Exception as e:
                pass

        if pitch_val is not None and yaw_val is not None:
            state = classify_head_pose(pitch_val, yaw_val)
        elif face_rect is not None:
            state = VisualAttentionState.FOCUSED_SCREEN

        # Draw Face Box
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

        # Distraction tracking
        if state == VisualAttentionState.DISTRACTED_PHONE:
            consecutive_distracted += 1
        elif state in (VisualAttentionState.FOCUSED_SCREEN, VisualAttentionState.FOCUSED_DESK_IPAD):
            consecutive_distracted = max(0, consecutive_distracted - 1)

        if consecutive_distracted >= 25: # ~2.5s sustained distraction
            if time.time() - last_banner_time > 8:
                last_banner_time = time.time()
                event_bus.publish("VISUAL_ATTENTION_STATE", state=state.value, is_distracted=True)

        # --- Draw HUD Overlay ---
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 95), (24, 24, 37), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Title
        cv2.putText(frame, "QuakMeeting Visual AI Focus Guardian (Apple Neural Engine)", (15, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (203, 166, 247), 2)

        # Status text & color
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

        cv2.putText(frame, f"State: {status_text}", (15, 56),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)
        cv2.putText(frame, f"Pitch: {p_deg:+.1f} deg | Yaw: {y_deg:+.1f} deg", (15, 82),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (166, 173, 200), 1)

        cv2.imshow("QuakMeeting Visual Attention Guardian", frame)

        key = cv2.waitKey(20) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Demo window closed.")

if __name__ == "__main__":
    main()
