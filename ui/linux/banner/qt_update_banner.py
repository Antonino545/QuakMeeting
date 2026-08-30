from __future__ import annotations

import sys
import math
from typing import Dict, Any

try:
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtCore import Qt, QTimer, QRect, QRectF
    from PyQt6.QtGui import (
        QColor, QPainter, QPen, QFont,
        QLinearGradient, QFontMetrics
    )
except ImportError:
    pass

from ui.linux.theme import Theme
from core.services.sound_service import play_chime

# ── Constants for Update Banner ──
CARD_W = 500
CARD_H = 148
CARD_R = 18
BTN_H = 32
BTN_JOIN_W = 170
BTN_SMALL_W = 100


class QtUpdateBannerWindow(QWidget):

    def __init__(self, event_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.pilot_type = event_data.get("pilot_type", "duck")
        self.action_url = event_data.get("action_url") or event_data.get("meeting_url")
        self.title = str(event_data.get("title", "Software Update"))
        self.provider = str(event_data.get("provider", "Software Update ✨"))
        self.btn_text = event_data.get("action_btn_text", "⚡ UPDATE NOW")
        self.quote_text = event_data.get("quote_text", "🚀 QuakMeeting Update Ready!")

        # Formatted time string
        st = event_data.get("start_time")
        self.time_str = st.strftime("At %H:%M") if hasattr(st, "strftime") else ""

        # ── Screen ──
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        self.screen_w = geo.width()
        self.screen_x = geo.x()
        self.screen_y = geo.y()

        self.tick = 0
        self.is_paused = False
        self._hover = None   # "join" | "snooze" | "close"

        self.install_mode = False
        self.install_progress = 0.0
        self.install_step = "Downloading..."
        self.install_ready = False

        try:
            from core.services.event_bus import event_bus
            event_bus.subscribe("UPDATE_STEP", self._on_update_step)
            event_bus.subscribe("UPDATE_PROGRESS", self._on_update_progress)
        except Exception:
            pass

        # ── Window setup ──
        self.win_w = CARD_W + 12
        self.win_h = CARD_H + 12
        self.setFixedSize(self.win_w, self.win_h)
        self.final_x = float(self.screen_x + self.screen_w - self.win_w - 24)
        self.final_y = float(self.screen_y + 24)
        self.win_x = self.final_x
        self.win_y = float(self.screen_y - self.win_h - 10)
        self.speed = 10.0
        self.stay_ticks = 0
        self.max_stay_ticks = 600  # 10s auto-dismiss

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.move(int(self.win_x), int(self.win_y))

        play_chime()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(16)

    def _on_update_step(self, step_id, step_name, **kwargs):
        self.install_step = step_name
        if step_id == "ready":
            self.install_ready = True
            self.stay_ticks = 0  # reset auto dismiss
            self.max_stay_ticks = 180  # dismiss 3s after ready

    def _on_update_progress(self, percent, **kwargs):
        self.install_progress = float(percent)

    # ── Animation ─────────────────────────────────────────────────────────────

    def _step(self):
        self.tick += 1

        if getattr(self, "is_closing", False):
            # Slide back UP out of the screen
            self.win_y -= self.speed * 1.8
            self.move(int(self.win_x), int(self.win_y))
            if self.win_y < self.screen_y - self.win_h - 20:
                self._finish_dismiss()
            else:
                self.update()
            return

        # Clean slide-down HUD animation
        if self.win_y < self.final_y:
            self.win_y = min(self.final_y, self.win_y + self.speed)
            self.move(int(self.win_x), int(self.win_y))
        else:
            self.move(int(self.win_x), int(self.final_y))
            if not self.is_paused:
                self.stay_ticks += 1
                if self.stay_ticks > self.max_stay_ticks:
                    self._dismiss()
        self.update()

    # ── Hit rects (window-local coords) ──────────────────────────────────────

    def _join_rect(self) -> QRectF:
        if getattr(self, "install_mode", False):
            return QRectF(0, 0, 0, 0)
        card_y = 6
        card_x = 6
        btn_y = card_y + CARD_H - BTN_H - 12
        btn_x0 = card_x + 16
        return QRectF(btn_x0, btn_y, BTN_JOIN_W, BTN_H)

    def _snooze_rect(self) -> QRectF:
        if getattr(self, "install_mode", False):
            return QRectF(0, 0, 0, 0)
        card_y = 6
        card_x = 6
        btn_y = card_y + CARD_H - BTN_H - 12
        btn_x0 = card_x + 16
        return QRectF(btn_x0 + BTN_JOIN_W + 8, btn_y, BTN_SMALL_W, BTN_H)

    def _close_rect(self) -> QRectF:
        s = 22
        card_y = 6
        card_x = 6
        return QRectF(card_x + CARD_W - s - 8, card_y + 8, s, s)

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, ev):
        p = ev.position()
        old = self._hover
        if self._close_rect().contains(p):
            self._hover = "close"
            self.is_paused = True
        elif self._join_rect().contains(p):
            self._hover = "join"
            self.is_paused = True
        elif self._snooze_rect().contains(p):
            self._hover = "snooze"
            self.is_paused = True
        elif QRectF(6, 6, CARD_W, CARD_H).contains(p):
            self._hover = None
            self.is_paused = True
        else:
            self._hover = None
            self.is_paused = False
        cur = Qt.CursorShape.PointingHandCursor if self._hover else Qt.CursorShape.ArrowCursor
        self.setCursor(cur)
        if old != self._hover:
            self.update()

    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        p = ev.position()
        if self._close_rect().contains(p):
            self._dismiss()
        elif self._join_rect().contains(p):
            if not self.install_mode:
                self.install_mode = True
                self.max_stay_ticks = 9999999  # prevent auto-dismiss during install
                from core.services.updater_service import updater_service
                updater_service.download_and_install_update(background=True)
        elif self._snooze_rect().contains(p):
            self._dismiss()

    def leaveEvent(self, ev):
        self.is_paused = False
        self._hover = None
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._draw_card(p)
        p.end()

    # ── Card ──────────────────────────────────────────────────────────────────

    def _draw_card(self, p: QPainter):
        cx = 6.0
        cy = 6.0
        card = QRectF(cx, cy, CARD_W, CARD_H)

        # ── Background ──
        p.setBrush(Theme.get_color('BASE', 245))
        # 🚀 Update Banner: Animated sweep border
        speed_mult = 5.0 if getattr(self, "install_mode", False) else 1.0
        phase = (math.sin(self.tick * 0.04 * speed_mult) + 1.0) / 2.0  # 0.0 to 1.0
        border_grad = QLinearGradient(cx, cy, cx + CARD_W, cy + CARD_H)
        c1 = Theme.BLUE
        c2 = Theme.get_color('MAUVE', 120)
        border_grad.setColorAt(0.0, c1 if phase < 0.5 else c2)
        border_grad.setColorAt(phase, Theme.TEXT)
        border_grad.setColorAt(1.0, c2 if phase < 0.5 else c1)
        p.setPen(QPen(border_grad, 2.5))
        
        p.drawRoundedRect(card, CARD_R, CARD_R)

        # ── Row 1: Provider pill + Close ──
        py = cy + 12.0

        # Provider pill
        prov_label = self.provider.upper()[:24]
        p.setFont(QFont("Inter, Arial", 9, QFont.Weight.ExtraBold))
        fm = QFontMetrics(p.font())
        pill_text_w = fm.horizontalAdvance(prov_label) + 24 + 12  # dot + text + padding
        pill_h = 22.0
        pill_x = cx + 14.0

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(Theme.SURFACE0)
        p.drawRoundedRect(QRectF(pill_x, py, pill_text_w, pill_h), 11, 11)
        # dot
        p.setBrush(Theme.BLUE)
        p.drawEllipse(QRectF(pill_x + 8, py + 7, 8, 8))
        # text
        p.setPen(Theme.TEXT)
        p.drawText(QRectF(pill_x + 22, py, pill_text_w - 22, pill_h),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   prov_label)

        # Close button ✕
        cr = self._close_rect()
        hover_close = self._hover == "close"
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(Theme.get_color('RED', 200) if hover_close else Theme.get_color('TEXT', 22))
        p.drawEllipse(cr)
        p.setPen(Theme.CRUST if hover_close else Theme.SUBTEXT0)
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        p.drawText(cr, Qt.AlignmentFlag.AlignCenter, "✕")

        # ── Row 2: Title ──
        p.setPen(Theme.TEXT)
        tf = QFont("Inter, Arial", 15)
        tf.setWeight(QFont.Weight.Bold)
        p.setFont(tf)
        title_rect = QRectF(cx + 14, cy + 40, CARD_W - 28, 26)
        fm_t = QFontMetrics(tf)
        elided = fm_t.elidedText(self.title, Qt.TextElideMode.ElideRight, int(CARD_W - 28))
        p.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)

        # ── Row 3: Subtitle ──
        sub_text = "⚡ Ready to download & install update"
        p.setPen(Theme.SUBTEXT0)
        sf = QFont("Inter, Arial", 10)
        p.setFont(sf)
        p.drawText(QRectF(cx + 14, cy + 68, CARD_W - 28, 20),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, sub_text)

        # ── Row 4: Action Buttons ──
        if getattr(self, "install_mode", False):
            pr = QRectF(cx + 16, cy + CARD_H - BTN_H - 12, CARD_W - 32, BTN_H)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(Theme.get_color('MANTLE', 200))
            p.drawRoundedRect(pr, 10, 10)

            if self.install_progress > 0:
                fill_w = (CARD_W - 32) * (self.install_progress / 100.0)
                fill_r = QRectF(pr.x(), pr.y(), fill_w, pr.height())
                fill_g = QLinearGradient(fill_r.topLeft(), fill_r.topRight())
                fill_g.setColorAt(0, Theme.BLUE)
                fill_g.setColorAt(1, Theme.MAUVE)
                p.setBrush(fill_g)
                p.drawRoundedRect(fill_r, 10, 10)

            p.setPen(Theme.CRUST)
            f = QFont("Inter, Arial", 10, QFont.Weight.Bold)
            p.setFont(f)
            if self.install_ready:
                status_txt = "✅ Update Installed! Relaunching..."
            else:
                status_txt = f"{self.install_step} {int(self.install_progress)}%"
            p.drawText(pr, Qt.AlignmentFlag.AlignCenter, status_txt)
            return  # skip drawing normal buttons
            
        jr = self._join_rect()
        hover_join = self._hover == "join"

        # Software update styling (vibrant cyan to electric blue gradient)
        g = QLinearGradient(jr.topLeft(), jr.topRight())
        if hover_join:
            g.setColorAt(0, Theme.BLUE)
            g.setColorAt(1, Theme.MAUVE)
        else:
            g.setColorAt(0, Theme.SAPPHIRE)
            g.setColorAt(1, Theme.BLUE)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(jr, 10, 10)
        p.setPen(Theme.CRUST)
        display_text = self.btn_text

        bf = QFont("Inter, Arial", 11)
        bf.setWeight(QFont.Weight.ExtraBold)
        p.setFont(bf)
        p.drawText(jr, Qt.AlignmentFlag.AlignCenter, display_text)

        mf = QFont("Inter, Arial", 10)
        mf.setWeight(QFont.Weight.Bold)

        sr = self._snooze_rect()
        hover_snz = self._hover == "snooze"
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(Theme.get_color('SURFACE1', 150) if hover_snz else Theme.SURFACE0)
        p.drawRoundedRect(sr, 10, 10)
        p.setPen(Theme.CRUST if hover_snz else Theme.SUBTEXT0)
        p.setFont(mf)
        p.drawText(sr, Qt.AlignmentFlag.AlignCenter, "✕ Later")

    # ── Dismiss ───────────────────────────────────────────────────────────────

    def _dismiss(self):
        self.is_closing = True

    def _finish_dismiss(self):
        self._timer.stop()
        self.close()
        from .qt_banner import _active_banners
        if self in _active_banners:
            _active_banners.remove(self)
        app = QApplication.instance()
        if app and "--test" in sys.argv:
            app.quit()


