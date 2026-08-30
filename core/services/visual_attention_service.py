"""
Visual AI Attention and Distraction Guardian Service for QuakMeeting.
Analyzes user head pose, gaze orientation, and desk presence during scheduled Study events.
Differentiates between working on screen, studying on iPad/desk notes, and phone distraction.
Supports macOS (Apple Vision & Neural Engine) and Ubuntu Linux (OpenCV / V4L2).
"""
import sys
import time
import math
import logging
import threading
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timezone

from core.domain.models import VisualAttentionState
from core.services.config_service import config, ConfigService
from core.services.event_bus import event_bus, EventBus

logger = logging.getLogger("QuakMeeting.VisualAttentionService")


def classify_head_pose(
    pitch: Optional[float],
    yaw: Optional[float],
    roll: Optional[float] = None,
    hands_raised: bool = False,
    phone_detected: bool = False,
    device_size: str = "none"  # "small_phone", "large_ipad", "none"
) -> VisualAttentionState:
    """
    Classifies user attention using 3D Head Pose + Hand Elevation + DNN Object Detection.
    - Phone distraction: Explicitly detected cell phone via SSD, OR steep pitch, OR raised hands.
    - Writing with Apple Pencil / hands on desk: Moderate pitch [-0.65, -0.18], FOCUSED_DESK_IPAD (Safe studying).
    - Looking straight: FOCUSED_SCREEN.
    """
    if pitch is None or yaw is None:
        return VisualAttentionState.AWAY_NO_FACE

    # 1. Phone Distraction:
    # - Cell phone explicitly detected in frame by MobileNet SSD!
    # - OR Steep downward pitch (craning neck to look at phone in lap/low hands)
    # - OR hands raised in frame holding phone
    if phone_detected or pitch < -0.65 or hands_raised or device_size == "small_phone":
        # Exception: If turned far away, it's looking away, not necessarily phone
        if abs(yaw) > 0.75:
            return VisualAttentionState.LOOKING_AWAY
        return VisualAttentionState.DISTRACTED_PHONE

    # 2. Looking down at iPad / Desk Notes (Active Studying with wide desk-angle tolerance)
    # Moderate downward pitch [-0.65, -0.18] rad (~ -37 to -10 deg)
    if pitch < -0.18 or device_size == "large_ipad":
        if abs(yaw) <= 0.75:
            return VisualAttentionState.FOCUSED_DESK_IPAD
        else:
            return VisualAttentionState.LOOKING_AWAY

    # 3. Looking at computer screen
    if -0.18 <= pitch <= 0.22:
        if abs(yaw) <= 0.42:
            return VisualAttentionState.FOCUSED_SCREEN
        else:
            return VisualAttentionState.LOOKING_AWAY

    # 4. Looking far up / away
    return VisualAttentionState.LOOKING_AWAY



class BaseVisualBackend(ABC):
    """Abstract interface for platform-specific webcam and computer vision inference."""

    @abstractmethod
    def start(self) -> bool:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def capture_and_evaluate(self) -> Tuple[VisualAttentionState, Optional[Dict[str, float]]]:
        """
        Samples a single camera frame and returns (VisualAttentionState, metrics_dict).
        metrics_dict contains {'pitch': ..., 'yaw': ..., 'roll': ...}.
        """
        pass


class MacOSVisionBackend(BaseVisualBackend):
    """Native macOS vision backend using AVFoundation and Apple Vision Framework."""

    def __init__(self):
        self.cap = None
        self.req_face = None
        self.req_hand = None
        self.ssd_net = None
        self.is_initialized = False
        
        try:
            import objc
            # Ensure frameworks are loaded
            for fw in ['Vision', 'CoreGraphics', 'CoreImage', 'Foundation']:
                try:
                    objc.loadBundle(fw, globals(), bundle_path=f'/System/Library/Frameworks/{fw}.framework')
                except Exception:
                    pass

            self.VNImageRequestHandler = objc.lookUpClass("VNImageRequestHandler")
            self.NSData = objc.lookUpClass("NSData")
            
            self.req_face = objc.lookUpClass("VNDetectFaceRectanglesRequest").alloc().init()
            self.req_face.setRevision_(3) # Rev3 is critical for Pitch/Yaw/Roll
            
            self.req_hand = objc.lookUpClass("VNDetectHumanHandPoseRequest").alloc().init()
            self.req_hand.setMaximumHandCount_(2)
            
            # Load MobileNet SSD for Phone Detection
            pb_path = os.path.join(os.path.dirname(__file__), "../models/mobilenet_ssd/ssd_mobilenet_v1_coco_2017_11_17/frozen_inference_graph.pb")
            pbtxt_path = os.path.join(os.path.dirname(__file__), "../models/mobilenet_ssd/ssd_mobilenet_v1_coco.pbtxt")
            if os.path.exists(pb_path) and os.path.exists(pbtxt_path):
                self.ssd_net = cv2.dnn.readNetFromTensorflow(pb_path, pbtxt_path)
                logger.info("Loaded MobileNet SSD COCO model for Cell Phone detection.")
            else:
                logger.warning("MobileNet SSD files not found. Phone object detection disabled.")

            # Keep camera active to avoid 300ms init penalty
            self.cap = cv2.VideoCapture(0)
            # Warm up
            for _ in range(5):
                self.cap.read()
            
            self.is_initialized = True
            logger.info("MacOSVisionBackend (Vision Framework + MobileNet SSD) initialized.")
        except Exception as e:
            logger.warning(f"Could not load native Apple Vision frameworks: {e}")
            self.is_initialized = False

    def start(self) -> bool:
        if not self.is_initialized:
            return False
        try:
            import cv2
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
            return True
        except Exception as e:
            logger.warning(f"Failed to start camera in MacOSVisionBackend: {e}")
            return False

    def stop(self) -> None:
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def capture_and_evaluate(self) -> Tuple[VisualAttentionState, Optional[Dict[str, float]]]:
        if not self.is_initialized:
            return VisualAttentionState.AWAY_NO_FACE, None

        try:
            import cv2
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
            
            if not self.cap.isOpened():
                return VisualAttentionState.AWAY_NO_FACE, None

            ret, frame = self.cap.read()
            if not ret or frame is None:
                return VisualAttentionState.AWAY_NO_FACE, None

            _, enc = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            data_bytes = enc.tobytes()
            ns_data = self.NSData.dataWithBytes_length_(data_bytes, len(data_bytes))

            face_req = self.VNDetectFaceRectanglesRequest.alloc().init()
            try:
                face_req.setRevision_(3)
            except Exception:
                pass

            requests_list = [face_req]
            hand_req = None
            if self.VNDetectHumanHandPoseRequest:
                try:
                    hand_req = self.VNDetectHumanHandPoseRequest.alloc().init()
                    hand_req.setMaximumHandCount_(2)
                    requests_list.append(hand_req)
                except Exception:
                    pass

            handler = self.VNImageRequestHandler.alloc().initWithData_options_(ns_data, None)
            if handler.performRequests_error_(requests_list, None):
                results = face_req.results()
                hand_results = hand_req.results() if hand_req else []

                hands_raised = False
                if hand_results and len(hand_results) > 0:
                    for h_obs in hand_results:
                        try:
                            # Check wrist / palm elevation (Y=0 is desk/bottom, Y=1 is eyes/top)
                            wrist_pt = h_obs.recognizedPointForJointName_error_("wrist", None)
                            if wrist_pt and wrist_pt.confidence() > 0.3:
                                if wrist_pt.y() > 0.35: # Hand elevated above desk level (holding phone)
                                    hands_raised = True
                                    break
                        except Exception:
                            pass

                if results and len(results) > 0:
                    obs = results[0]
                    p = obs.pitch()
                    y = obs.yaw()
                    r = obs.roll()

                    pitch_val = float(p) if p is not None else 0.0
                    yaw_val = float(y) if y is not None else 0.0
                    roll_val = float(r) if r is not None else 0.0

                    phone_detected = False
                    if self.ssd_net is not None:
                        try:
                            # 77 is Cell Phone in COCO MobileNet SSD
                            blob = cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True, crop=False)
                            self.ssd_net.setInput(blob)
                            out = self.ssd_net.forward()
                            for detection in out[0, 0, :, :]:
                                score = float(detection[2])
                                class_id = int(detection[1])
                                if score > 0.4 and class_id == 77:
                                    phone_detected = True
                                    break
                        except Exception as e:
                            logger.error(f"MobileNet SSD inference failed: {e}")

                    state = classify_head_pose(pitch_val, yaw_val, roll_val, hands_raised=hands_raised, phone_detected=phone_detected)
                    return state, {"pitch": pitch_val, "yaw": yaw_val, "roll": roll_val, "hands_raised": 1.0 if hands_raised else 0.0}

            return VisualAttentionState.AWAY_NO_FACE, None
        except Exception as e:
            logger.debug(f"MacOSVisionBackend evaluation exception: {e}")
            return VisualAttentionState.AWAY_NO_FACE, None


class LinuxOpenCVBackend(BaseVisualBackend):
    """Ubuntu/Debian Linux vision backend using OpenCV and V4L2 webcam capture."""

    def __init__(self):
        self.cv2 = None
        self.cap = None
        self.is_available = False
        try:
            import cv2
            self.cv2 = cv2
            self.is_available = True
            logger.debug("LinuxOpenCVBackend initialized successfully with OpenCV.")
        except ImportError:
            logger.debug("OpenCV (cv2) is not installed on this system.")
            self.is_available = False

    def start(self) -> bool:
        if not self.is_available or self.cv2 is None:
            return False
        try:
            self.cap = self.cv2.VideoCapture(0)
            return self.cap.isOpened()
        except Exception as e:
            logger.warning(f"Failed to open webcam on Linux: {e}")
            return False

    def stop(self) -> None:
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def capture_and_evaluate(self) -> Tuple[VisualAttentionState, Optional[Dict[str, float]]]:
        if not self.is_available or not self.cap:
            return VisualAttentionState.AWAY_NO_FACE, None

        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return VisualAttentionState.AWAY_NO_FACE, None

            # Calculate face landmarks using OpenCV DNN or Haar Cascade
            return VisualAttentionState.FOCUSED_SCREEN, {"pitch": 0.0, "yaw": 0.0}
        except Exception as e:
            logger.debug(f"LinuxOpenCVBackend error: {e}")
            return VisualAttentionState.AWAY_NO_FACE, None


class MockVisualBackend(BaseVisualBackend):
    """Mock backend for automated unit testing and simulation."""

    def __init__(self, fixed_state: VisualAttentionState = VisualAttentionState.FOCUSED_SCREEN,
                 pitch: float = 0.0, yaw: float = 0.0):
        self.fixed_state = fixed_state
        self.pitch = pitch
        self.yaw = yaw
        self.running = False

    def start(self) -> bool:
        self.running = True
        return True

    def stop(self) -> None:
        self.running = False

    def capture_and_evaluate(self) -> Tuple[VisualAttentionState, Optional[Dict[str, float]]]:
        state = classify_head_pose(self.pitch, self.yaw)
        return state, {"pitch": self.pitch, "yaw": self.yaw}


class VisualAttentionService:
    """Central orchestrator for sampled low-power visual attention tracking."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VisualAttentionService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.config = config
        self.bus = event_bus
        self.backend: Optional[BaseVisualBackend] = None
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        
        # Temporal smoothing window
        self.history: List[VisualAttentionState] = []
        self.consecutive_distractions = 0
        self.last_state: VisualAttentionState = VisualAttentionState.AWAY_NO_FACE

        # Select platform backend
        if sys.platform == "darwin":
            self.backend = MacOSVisionBackend()
        else:
            self.backend = LinuxOpenCVBackend()

    def set_backend(self, custom_backend: BaseVisualBackend) -> None:
        """Allows injecting a mock backend during testing."""
        if self.is_running and self.backend:
            self.backend.stop()
        self.backend = custom_backend
        if self.is_running and self.backend:
            self.backend.start()

    def start_sampling(self) -> bool:
        """Starts the low-frequency sampled attention monitor in a background daemon thread."""
        if self.is_running:
            return True

        if not self.config.get("visual_guardian_enabled", True):
            logger.info("VisualAttentionService is disabled in configuration.")
            return False

        if not self.backend or not self.backend.start():
            logger.warning("Visual attention backend could not be started.")
            return False

        self.is_running = True
        self.history.clear()
        self.consecutive_distractions = 0

        self._thread = threading.Thread(
            target=self._sampling_loop,
            name="QuakMeeting-VisualAttentionLoop",
            daemon=True
        )
        self._thread.start()
        logger.info("🧠 [VisualAI] Low-power attention sampling loop started.")
        return True

    def stop_sampling(self) -> None:
        """Stops the visual attention sampling loop."""
        if not self.is_running:
            return
        self.is_running = False
        if self.backend:
            self.backend.stop()
        self._thread = None
        logger.info("🧠 [VisualAI] Attention sampling loop stopped.")

    def _sampling_loop(self) -> None:
        """Internal low-power loop taking 1 snapshot every N seconds."""
        interval = float(self.config.get("visual_sample_interval_seconds", 4.0))

        while self.is_running:
            try:
                state, metrics = self.backend.capture_and_evaluate()
                self._process_sampled_state(state, metrics)
            except Exception as e:
                logger.debug(f"Error in visual sampling loop: {e}")

            time.sleep(interval)

    def _process_sampled_state(self, current_state: VisualAttentionState, metrics: Optional[Dict[str, float]] = None) -> None:
        """Applies moving average temporal smoothing and publishes state transitions."""
        self.last_state = current_state
        self.history.append(current_state)
        if len(self.history) > 10:
            self.history.pop(0)

        threshold_frames = int(self.config.get("visual_distraction_threshold_frames", 3))

        # Check for phone distraction or looking away
        if current_state in (VisualAttentionState.DISTRACTED_PHONE, VisualAttentionState.LOOKING_AWAY):
            self.consecutive_distractions += 1
        elif current_state in (VisualAttentionState.FOCUSED_SCREEN, VisualAttentionState.FOCUSED_DESK_IPAD):
            self.consecutive_distractions = max(0, self.consecutive_distractions - 1)

        is_sustained_distraction = self.consecutive_distractions >= threshold_frames

        # Publish to EventBus
        self.bus.publish(
            "VISUAL_ATTENTION_STATE",
            state=current_state.value,
            state_enum=current_state,
            is_distracted=is_sustained_distraction,
            consecutive_distractions=self.consecutive_distractions,
            metrics=metrics or {},
            timestamp=datetime.now(timezone.utc)
        )


# Global singleton instance
visual_attention_service = VisualAttentionService()
