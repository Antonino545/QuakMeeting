"""
Unit tests for VisualAttentionService (Head-Pose Math, Attention States, and Temporal Smoothing).
"""
import unittest
import time
from core.domain.models import VisualAttentionState
from core.services.visual_attention_service import (
    classify_head_pose,
    VisualAttentionService,
    MockVisualBackend
)
from core.services.event_bus import EventBus
from core.services.config_service import ConfigService


class TestVisualAttentionService(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.config = ConfigService()
        self.service = VisualAttentionService()
        self.service.bus = self.bus
        self.service.config = self.config

    def tearDown(self):
        self.service.stop_sampling()

    def test_head_pose_classification_math(self):
        # 1. Screen Focus (Level pitch)
        self.assertEqual(classify_head_pose(0.0, 0.0), VisualAttentionState.FOCUSED_SCREEN)
        self.assertEqual(classify_head_pose(0.15, -0.10), VisualAttentionState.FOCUSED_SCREEN)

        # 2. Desk / iPad Focus (Moderate downward tilt: -0.18 to -0.65)
        self.assertEqual(classify_head_pose(-0.35, 0.05), VisualAttentionState.FOCUSED_DESK_IPAD)
        self.assertEqual(classify_head_pose(-0.50, -0.15), VisualAttentionState.FOCUSED_DESK_IPAD)
        self.assertEqual(classify_head_pose(-0.60, 0.0), VisualAttentionState.FOCUSED_DESK_IPAD)
        self.assertEqual(classify_head_pose(-0.30, 0.0, device_size="large_ipad"), VisualAttentionState.FOCUSED_DESK_IPAD)

        # 3. Phone Distraction (Steep downward tilt < -0.65 OR hands raised)
        self.assertEqual(classify_head_pose(-0.75, 0.0), VisualAttentionState.DISTRACTED_PHONE)
        self.assertEqual(classify_head_pose(-0.85, 0.10), VisualAttentionState.DISTRACTED_PHONE)
        self.assertEqual(classify_head_pose(-0.30, 0.0, hands_raised=True), VisualAttentionState.DISTRACTED_PHONE)
        self.assertEqual(classify_head_pose(-0.25, 0.0, device_size="small_phone"), VisualAttentionState.DISTRACTED_PHONE)

        # 4. Looking Away (Turned head away from screen & desk)
        self.assertEqual(classify_head_pose(0.0, 0.55), VisualAttentionState.LOOKING_AWAY)
        self.assertEqual(classify_head_pose(-0.20, -0.80), VisualAttentionState.LOOKING_AWAY)

        # 5. Missing Face
        self.assertEqual(classify_head_pose(None, None), VisualAttentionState.AWAY_NO_FACE)

    def test_mock_backend_and_temporal_smoothing(self):
        # Setup mock backend reporting phone distraction
        mock_backend = MockVisualBackend(pitch=-0.80, yaw=0.0)
        self.service.set_backend(mock_backend)

        published_events = []
        self.bus.subscribe("VISUAL_ATTENTION_STATE", lambda **kwargs: published_events.append(kwargs))

        # 1 frame: not yet sustained distraction (threshold is 3)
        self.service._process_sampled_state(VisualAttentionState.DISTRACTED_PHONE, {"pitch": -0.80, "yaw": 0.0})
        self.assertEqual(len(published_events), 1)
        self.assertFalse(published_events[-1].get("is_distracted"))
        self.assertEqual(published_events[-1].get("consecutive_distractions"), 1)

        # 2 frames
        self.service._process_sampled_state(VisualAttentionState.DISTRACTED_PHONE, {"pitch": -0.80, "yaw": 0.0})
        self.assertFalse(published_events[-1].get("is_distracted"))
        self.assertEqual(published_events[-1].get("consecutive_distractions"), 2)

        # 3 frames: threshold reached! Sustained distraction!
        self.service._process_sampled_state(VisualAttentionState.DISTRACTED_PHONE, {"pitch": -0.80, "yaw": 0.0})
        self.assertTrue(published_events[-1].get("is_distracted"))
        self.assertEqual(published_events[-1].get("consecutive_distractions"), 3)

        # User looks back at iPad / Desk: consecutive count decreases
        self.service._process_sampled_state(VisualAttentionState.FOCUSED_DESK_IPAD, {"pitch": -0.35, "yaw": 0.0})
        self.assertEqual(published_events[-1].get("consecutive_distractions"), 2)


if __name__ == "__main__":
    unittest.main()
