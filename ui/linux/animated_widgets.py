"""
Rock-Solid, Glitch-Free PyQt6 Animations for QuakMeeting Flight Deck.
- Event-driven: Timers ONLY run when active, 0 overhead when idle.
- Zero QGraphicsOpacityEffect: Eliminates Linux compositor font blur, tearing, and black box glitches.
- UpdatingHUDWidget: High-energy animated update HUD with flying mascot jet, exhaust flames, phase tracking & gears.
- Clean QPainter pipelines with proper state preservation.
"""
from __future__ import annotations
from ui.linux.theme import Theme

import math
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QProgressBar, QFrame
)
from PyQt6.QtCore import (
    Qt, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve, pyqtProperty
)
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont, QPixmap,
    QLinearGradient, QRadialGradient, QPainterPath
)

logger = logging.getLogger("QuakMeeting.AnimatedWidgets")


class BouncingMascotLabel(QLabel):
    """
    Mascot Avatar with on-open welcome bounce and interactive click/hover reaction.
    Timer ONLY runs during active bounce (auto-stops when resting).
    """

    def __init__(self, pixmap: Optional[QPixmap] = None, emoji: str = "🦆", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.raw_pixmap = pixmap
        self.emoji = emoji
        self.setFixedSize(54, 54)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("QuakMeeting Mascot — Click for a bounce! 🦆")

        self._bounce_step = 0
        self._max_steps = 30
        self._is_bouncing = False
        self._scale = 1.0
        self._offset_y = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_bounce_tick)

        # Trigger welcome bounce on launch
        self.trigger_bounce()

    def trigger_bounce(self):
        """Starts a clean, smooth spring bounce animation that auto-stops."""
        if not self._is_bouncing:
            self._is_bouncing = True
            self._bounce_step = 0
            self._timer.start(20)

    def _on_bounce_tick(self):
        self._bounce_step += 1
        t = self._bounce_step / self._max_steps  # 0.0 -> 1.0

        if t >= 1.0:
            self._is_bouncing = False
            self._offset_y = 0.0
            self._scale = 1.0
            self._timer.stop()
        else:
            # Smooth spring bounce curve
            decay = math.exp(-t * 4.0)
            self._offset_y = -math.sin(t * math.pi * 3.0) * decay * 10.0
            self._scale = 1.0 + (math.cos(t * math.pi * 3.0) * decay * 0.12)

        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.trigger_bounce()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = float(self.width()), float(self.height())
        cx = w / 2.0
        cy = h / 2.0 + self._offset_y

        painter.save()
        painter.translate(cx, cy)
        painter.scale(self._scale, self._scale)
        painter.translate(-cx, -cy)

        if self.raw_pixmap and not self.raw_pixmap.isNull():
            pw = float(self.raw_pixmap.width())
            ph = float(self.raw_pixmap.height())
            target_w = min(46.0, pw)
            target_h = min(46.0, ph)
            px = (w - target_w) / 2.0
            py = (h - target_h) / 2.0
            painter.drawPixmap(int(px), int(py), int(target_w), int(target_h), self.raw_pixmap)
        else:
            painter.setFont(QFont("sans-serif", 30))
            painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.emoji)

        painter.restore()


class AnimatedSpinButton(QPushButton):
    """
    Button with animated spinning indicator during async actions,
    and timed success/failure feedback badge.
    Timer ONLY runs while spinning.
    """

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, text: str = "🔄 Sync Now", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._default_text = text
        self._is_spinning = False
        self._spin_index = 0
        self._prefix = ""

        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._on_spin_tick)

        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._on_reset_timeout)

    def start_spinning(self, loading_text: str = "Syncing..."):
        self._is_spinning = True
        self._prefix = loading_text
        self._spin_index = 0
        self.setEnabled(False)
        self._spin_timer.start(80)

    def stop_spinning(self, result_text: Optional[str] = None, is_success: bool = True, reset_delay_ms: int = 2000):
        self._is_spinning = False
        self._spin_timer.stop()
        self.setEnabled(True)

        if result_text is not None:
            self.setText(result_text)
            self._reset_timer.start(reset_delay_ms)
        else:
            self.setText(self._default_text)

    def _on_spin_tick(self):
        frame = self.SPINNER_FRAMES[self._spin_index % len(self.SPINNER_FRAMES)]
        self._spin_index += 1
        self.setText(f"{frame} {self._prefix}")

    def _on_reset_timeout(self):
        self.setText(self._default_text)


class AnimatedUpdateCard(QFrame):
    """
    Software Update Card with animated sweep during scanning.
    Timer ONLY runs while actively scanning.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._is_scanning = False
        self._scan_phase = 0.0
        self._has_update = False
        self._is_up_to_date = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    def set_scanning(self, active: bool):
        self._is_scanning = active
        self._has_update = False
        self._is_up_to_date = False
        if active:
            self._scan_phase = 0.0
            self._timer.start(30)
        else:
            self._timer.stop()
        self.update()

    def set_update_available(self, version: str):
        self._is_scanning = False
        self._timer.stop()
        self._has_update = True
        self._is_up_to_date = False
        self.update()

    def set_up_to_date(self):
        self._is_scanning = False
        self._timer.stop()
        self._has_update = False
        self._is_up_to_date = True
        self.update()

    def _on_tick(self):
        if self._is_scanning:
            self._scan_phase = (self._scan_phase + 0.03) % 1.0
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw dynamic glowing radar sweep line only while scanning
        if self._is_scanning:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            w = float(self.width())
            sweep_x = self._scan_phase * w
            sweep_grad = QLinearGradient(sweep_x - 80, 0, sweep_x + 80, 0)
            sweep_grad.setColorAt(0.0, Theme.get_color('BLUE', 0))
            sweep_grad.setColorAt(0.5, Theme.get_color('BLUE', 240))
            sweep_grad.setColorAt(1.0, Theme.get_color('BLUE', 0))

            painter.setPen(QPen(sweep_grad, 2.5))
            painter.drawLine(int(max(0, sweep_x - 80)), 1, int(min(w, sweep_x + 80)), 1)


class UpdatingHUDWidget(QFrame):
    """
    Rich Animated HUD displayed while QuakMeeting is updating itself.
    Features:
    - 4-Phase Step pipeline (1. Connect -> 2. Download -> 3. Install -> 4. Ready)
    - Flying Mascot Jet Rocket moving across the progress bar track
    - Glowing rocket thruster exhaust particles
    - Rotating gears during package installation
    - Real-time MB and percentage readouts
    """

    PHASES = ["📡 Connect", "📥 Download", "⚙️ Install", "🎉 Ready"]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(118)
        self.setStyleSheet("background: rgba(24, 24, 37, 0.6); border: 1px solid rgba(137, 180, 250, 0.25); border-radius: 12px;")

        self._phase_index = 1  # 0: Connect, 1: Download, 2: Install, 3: Ready
        self._percent = 0.0
        self._target_percent = 0.0
        self._downloaded = 0
        self._total = 0
        self._tick = 0
        self._gear_angle = 0.0
        self._status_caption = "Downloading update package..."

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    def start_downloading(self, file_name: str = ""):
        """Starts animated download HUD phase."""
        self._phase_index = 1
        self._target_percent = 5.0
        self._percent = 5.0
        self._downloaded = 0
        self._total = 0
        self._status_caption = f"Downloading {file_name}..." if file_name else "Downloading update package..."
        self.setVisible(True)
        if not self._timer.isActive():
            self._timer.start(25)
        self.update()

    def set_progress(self, percent: int, downloaded: int = 0, total: int = 0):
        """Updates live download progress with smooth jet tracking."""
        self._phase_index = 1
        self._target_percent = float(max(0, min(100, percent)))
        self._downloaded = downloaded
        self._total = total
        mb_d = downloaded / (1024 * 1024) if downloaded > 0 else 0
        mb_t = total / (1024 * 1024) if total > 0 else 0
        if mb_t > 0:
            self._status_caption = f"Downloading: {mb_d:.1f} MB / {mb_t:.1f} MB ({percent}%)"
        else:
            self._status_caption = f"Downloading: {percent}%"
        self.setVisible(True)
        if not self._timer.isActive():
            self._timer.start(25)
        self.update()

    def set_installing(self):
        """Switches HUD to the package installation & verification step."""
        self._phase_index = 2
        self._target_percent = 100.0
        self._status_caption = "Installing & verifying package with system privileges..."
        self.setVisible(True)
        if not self._timer.isActive():
            self._timer.start(25)
        self.update()

    def set_installed(self):
        """Switches HUD to the completed / relaunch step."""
        self._phase_index = 3
        self._target_percent = 100.0
        self._status_caption = "Update installed successfully! Relaunching QuakMeeting..."
        self.setVisible(True)
        self.update()
        QTimer.singleShot(4000, self._auto_stop)

    def _auto_stop(self):
        self._timer.stop()

    def _on_tick(self):
        self._tick += 1
        # Smooth interpolation towards target percent
        diff = self._target_percent - self._percent
        if abs(diff) > 0.2:
            self._percent += diff * 0.18
        else:
            self._percent = self._target_percent

        self._gear_angle = (self._gear_angle + 6.0) % 360.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = float(self.width())
        h = float(self.height())

        # ── 1. Top Phase Step Pills ───────────────────────────────────────────
        pill_y = 12.0
        pill_h = 22.0
        num_phases = len(self.PHASES)
        margin = 16.0
        gap = 8.0
        available_w = w - (margin * 2.0) - (gap * (num_phases - 1))
        pill_w = available_w / float(num_phases)

        for i, name in enumerate(self.PHASES):
            px = margin + (i * (pill_w + gap))
            p_rect = QRectF(px, pill_y, pill_w, pill_h)

            if i < self._phase_index:
                # Completed step (emerald green)
                bg_col = Theme.get_color('GREEN', 45)
                border_col = Theme.get_color('GREEN', 140)
                text_col = Theme.GREEN
                label = "✓ " + name.split(" ", 1)[-1]
            elif i == self._phase_index:
                # Active step (electric cyan with breathing pulse)
                pulse = 0.5 + 0.5 * math.sin(self._tick * 0.15)
                bg_col = Theme.get_color('SAPPHIRE', int(60 + pulse * 45))
                border_col = Theme.get_color('BLUE', int(160 + pulse * 95))
                text_col = Theme.TEXT
                label = name
            else:
                # Pending step (dim grey)
                bg_col = Theme.get_color('TEXT', 10)
                border_col = Theme.get_color('TEXT', 25)
                text_col = Theme.SUBTEXT0
                label = name

            painter.setPen(QPen(border_col, 1.0))
            painter.setBrush(bg_col)
            painter.drawRoundedRect(p_rect, 11.0, 11.0)

            painter.setPen(text_col)
            painter.setFont(QFont("sans-serif", 9, QFont.Weight.Bold))
            painter.drawText(p_rect, Qt.AlignmentFlag.AlignCenter, label)

        # ── 2. Progress Bar Track & Flying Jet ────────────────────────────────
        track_x = margin
        track_y = 52.0
        track_w = w - (margin * 2.0)
        track_h = 16.0
        track_rect = QRectF(track_x, track_y, track_w, track_h)

        # Background track
        painter.setPen(QPen(Theme.get_color('BLUE', 60), 1.0))
        painter.setBrush(Theme.get_color('MANTLE', 230))
        painter.drawRoundedRect(track_rect, 8.0, 8.0)

        # Filled Chunk
        pct = max(0.0, min(1.0, self._percent / 100.0))
        if pct > 0.005:
            fill_w = max(16.0, track_w * pct)
            fill_rect = QRectF(track_x + 1.0, track_y + 1.0, fill_w - 2.0, track_h - 2.0)

            chunk_grad = QLinearGradient(track_x, 0, track_x + fill_w, 0)
            chunk_grad.setColorAt(0.0, Theme.SAPPHIRE)
            chunk_grad.setColorAt(0.7, Theme.BLUE)
            chunk_grad.setColorAt(1.0, Theme.MAUVE)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(chunk_grad)
            painter.drawRoundedRect(fill_rect, 7.0, 7.0)

        # ── Flying Mascot Jet over the Progress Bar ───────────────────────────
        jet_cx = track_x + (track_w * pct)
        jet_cy = track_y + (track_h / 2.0)

        # Thruster exhaust flame (pulsing orange/yellow glow cone behind jet)
        flame_len = 14.0 + math.sin(self._tick * 0.4) * 6.0
        flame_path = QPainterPath()
        flame_path.moveTo(jet_cx - 8.0, jet_cy - 4.0)
        flame_path.lineTo(jet_cx - 8.0 - flame_len, jet_cy)
        flame_path.lineTo(jet_cx - 8.0, jet_cy + 4.0)
        flame_path.closeSubpath()

        flame_grad = QLinearGradient(jet_cx - 8.0, 0, jet_cx - 8.0 - flame_len, 0)
        flame_grad.setColorAt(0.0, Theme.get_color('YELLOW', 230))
        flame_grad.setColorAt(0.6, Theme.get_color('PEACH', 180))
        flame_grad.setColorAt(1.0, Theme.get_color('RED', 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(flame_grad)
        painter.drawPath(flame_path)

        # Mascot Avatar Jet
        if self._phase_index == 2:
            # Installing: Spinning gear icon
            painter.save()
            painter.translate(jet_cx, jet_cy)
            painter.rotate(self._gear_angle)
            painter.setFont(QFont("sans-serif", 16))
            painter.setPen(Theme.TEXT)
            painter.drawText(QRectF(-12, -12, 24, 24), Qt.AlignmentFlag.AlignCenter, "⚙️")
            painter.restore()
        elif self._phase_index == 3:
            # Completed: Confetti Star
            painter.setFont(QFont("sans-serif", 18))
            painter.setPen(Theme.TEXT)
            painter.drawText(QRectF(jet_cx - 14, jet_cy - 14, 28, 28), Qt.AlignmentFlag.AlignCenter, "🎉")
        else:
            # Downloading: Flying Jet Duck
            painter.setFont(QFont("sans-serif", 16))
            painter.setPen(Theme.TEXT)
            painter.drawText(QRectF(jet_cx - 12, jet_cy - 14, 24, 24), Qt.AlignmentFlag.AlignCenter, "🚀")

        # ── 3. Bottom Status & Readout Row ────────────────────────────────────
        bottom_y = 86.0
        painter.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        painter.setPen(Theme.TEXT)
        painter.drawText(QRectF(margin + 4.0, bottom_y, w - 120.0, 22.0),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         self._status_caption)

        pct_label = f"{int(self._percent)}%"
        painter.setPen(Theme.BLUE)
        painter.drawText(QRectF(w - margin - 80.0, bottom_y, 76.0, 22.0),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                         pct_label)


class ToggleSwitch(QWidget):
    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self._checked = checked
        self._pos = 22.0 if checked else 2.0
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled = None # Custom signal/callback

    @pyqtProperty(float)
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, val):
        self._pos = val
        self.update()

    def isChecked(self):
        return self._checked

    def setChecked(self, val):
        self._checked = val
        self._pos = 22.0 if val else 2.0
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self._anim.setEndValue(22.0 if self._checked else 2.0)
            self._anim.start()
            if self.toggled:
                self.toggled(self._checked)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Catppuccin Mocha colors
        c_off = Theme.SURFACE0 # Surface0
        c_on = Theme.MAUVE  # Mauve
        c_knob = Theme.CRUST if self._checked else Theme.TEXT

        bg = c_on if self._checked else c_off
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)

        p.setBrush(c_knob)
        p.drawEllipse(QRectF(self._pos, 2.0, 20.0, 20.0))
        p.end()
