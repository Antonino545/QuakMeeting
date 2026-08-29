from __future__ import annotations
from ui.linux.theme import Theme
import sys
import os
import math
import webbrowser
from datetime import datetime
from typing import Dict, Any

try:
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, QPointF
    from PyQt6.QtGui import (
        QColor, QPainter, QBrush, QPen, QFont, QPainterPath,
        QLinearGradient, QRadialGradient, QFontMetrics
    )
except ImportError:
    pass

from .qt_banner import (
    PILOT_QUOTES, PILOT_COLORS, PROVIDER_DOTS,
    CARD_W, CARD_H, CARD_R, CABLE_LEN, PLANE_SPAN, WIN_W, WIN_H,
    CARD_X, CARD_Y, PLANE_CX, PLANE_CY, BTN_H, BTN_Y, BTN_X0,
    BTN_JOIN_W, BTN_SMALL_W, BTN_ARR_W, BTN_SNOOZE_W, BTN_GAP,
    BTN_ARRIVE_X, BTN_SNOOZE_X, CLOSE_R, CLOSE_CX, CLOSE_CY
)

# ── Main Banner Widget ────────────────────────────────────────────────────────


class QtUpdateBannerWindow(QWidget):

    def __init__(self, event_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.event_data  = event_data
        self.pilot_type  = event_data.get("pilot_type", "duck")
        self.action_url  = event_data.get("action_url") or event_data.get("meeting_url")
        self.title       = str(event_data.get("title", "Upcoming Event"))
        self.provider    = str(event_data.get("provider", "Calendar"))
        self.btn_text    = event_data.get("action_btn_text", "🚀 JOIN MEETING")
        self.is_late     = bool(event_data.get("is_late", False))
        self.is_travel   = bool(event_data.get("is_travel", False))
        self.is_update_banner = bool(event_data.get("is_update_banner", False))
        self.quote_text  = event_data.get("quote_text") or PILOT_QUOTES.get(self.pilot_type, "🚀 Meeting starting soon!")

        # Formatted time string
        st = event_data.get("start_time")
        self.time_str = st.strftime("At %H:%M") if hasattr(st, "strftime") else ""
        self.classroom = str(event_data.get("classroom") or "")
        self.reminder_stage = event_data.get("reminder_stage")

        self.has_real_url = bool(
            self.action_url and
            self.action_url.strip() and
            self.action_url != "https://calendar.apple.com"
        )
        self.has_maps_url = bool(
            self.action_url and ("maps.apple.com" in self.action_url or "maps.google.com" in self.action_url or "google.com/maps" in self.action_url)
        ) or self.is_travel

        # ── Screen ──
        screen = QApplication.primaryScreen()
        geo    = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        self.screen_w = geo.width()
        self.screen_x = geo.x()
        self.screen_y = geo.y()

        self.tick      = 0
        self.is_paused = False
        self._hover    = None   # "join" | "arrive" | "snooze" | "close"

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
        if self.is_update_banner:
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
        else:
            self.win_w = WIN_W
            self.win_h = WIN_H
            self.setFixedSize(WIN_W, WIN_H)
            self.win_x = float(self.screen_x - WIN_W - 20)
            self.win_y = float(self.screen_y + 14)
            self.speed = 3.8

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

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(16)


    def _on_update_step(self, step_id, step_name, **kwargs):
        self.install_step = step_name
        if step_id == "ready":
            self.install_ready = True
            self.stay_ticks = 0 # reset auto dismiss
            self.max_stay_ticks = 180 # dismiss 3s after ready

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

        if self.is_update_banner:
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
        else:
            if not self.is_paused:
                self.win_x += self.speed
            bob = math.sin(self.tick * 0.035) * 5
            self.move(int(self.win_x), int(self.win_y + bob))
            if self.win_x > self.screen_x + self.screen_w + 20:
                if self.reminder_stage is not None and self.reminder_stage > 0:
                    self._dismiss()
                else:
                    self.win_x = float(self.screen_x - WIN_W - 20)
            else:
                self.update()

    # ── Hit rects (window-local coords) ──────────────────────────────────────

    def _join_rect(self)   -> QRectF:
        if getattr(self, "install_mode", False): return QRectF(0,0,0,0)
        card_y = 6
        card_x = 6
        btn_y  = card_y + CARD_H - BTN_H - 12
        btn_x0 = card_x + 16
        return QRectF(btn_x0, btn_y, BTN_JOIN_W, BTN_H)

    def _arrive_rect(self) -> QRectF:
        if self.has_maps_url and not self.is_update_banner:
            return QRectF(BTN_ARRIVE_X, BTN_Y, BTN_SMALL_W, BTN_H)
        return QRectF(0, 0, 0, 0)

    def _snooze_rect(self) -> QRectF:
        if getattr(self, "install_mode", False): return QRectF(0,0,0,0)
        if self.is_update_banner:
            card_y = 6
            card_x = 6
            btn_y  = card_y + CARD_H - BTN_H - 12
            btn_x0 = card_x + 16
            return QRectF(btn_x0 + BTN_JOIN_W + 8, btn_y, BTN_SMALL_W, BTN_H)
        if self.reminder_stage == 0 and not self.has_real_url:
            return QRectF(0, 0, 0, 0)
        if self.has_maps_url:
            return QRectF(BTN_SNOOZE_X, BTN_Y, BTN_SMALL_W, BTN_H)
        return QRectF(BTN_ARRIVE_X, BTN_Y, BTN_SMALL_W, BTN_H)

    def _close_rect(self)  -> QRectF:
        s = 22
        card_y = 6
        card_x = 6
        return QRectF(card_x + CARD_W - s - 8, card_y + 8, s, s)

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, ev):
        p = ev.position()
        old = self._hover
        if   self._close_rect().contains(p):  self._hover = "close";  self.is_paused = True
        elif self._join_rect().contains(p):    self._hover = "join";   self.is_paused = True
        elif self._arrive_rect().contains(p):  self._hover = "arrive"; self.is_paused = True
        elif self._snooze_rect().contains(p):  self._hover = "snooze"; self.is_paused = True
        elif QRectF(CARD_X, CARD_Y, CARD_W, CARD_H).contains(p):
            self._hover = None; self.is_paused = True
        else:
            self._hover = None; self.is_paused = False
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
        elif self._arrive_rect().contains(p):
            meeting_id = self.event_data.get("id")
            if meeting_id:
                try:
                    from core.services.event_bus import event_bus
                    event_bus.publish("MARK_ARRIVED", meeting_id=meeting_id)
                except Exception:
                    pass
            self._dismiss()
        elif self._snooze_rect().contains(p):
            # If the button says "Got it", it means we want to ignore completely
            if self.reminder_stage == 0 or not self.has_real_url:
                meeting_id = self.event_data.get("id")
                if meeting_id:
                    try:
                        from core.services.event_bus import event_bus
                        event_bus.publish("MARK_ARRIVED", meeting_id=meeting_id)
                    except Exception:
                        pass
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
        if not self.is_update_banner:
            self._draw_cable(p)
        self._draw_card(p)
        if not self.is_update_banner:
            self._draw_plane(p, PLANE_CX, PLANE_CY)
            self._draw_bubble(p, PLANE_CX, PLANE_CY)
        p.end()

    # ── Card ──────────────────────────────────────────────────────────────────

    def _draw_card(self, p: QPainter):
        cx = 6.0
        cy = 6.0
        card = QRectF(cx, cy, CARD_W, CARD_H)

        # ── Background ──
        p.setBrush(Theme.get_color('BASE', 245))
        if self.is_update_banner:
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
        else:
            # 🦆 Duck Banner: No border
            p.setPen(Qt.PenStyle.NoPen)
        
        p.drawRoundedRect(card, CARD_R, CARD_R)

        # Gear removed by user request
        # ── Row 1: Provider pill + Status pill + Close ──
        py = cy + 12.0

        # Provider pill
        prov_lower = self.provider.lower()
        dot_color = Theme.BLUE
        for k, c in PROVIDER_DOTS.items():
            if k in prov_lower:
                dot_color = c
                break
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
        p.setBrush(dot_color)
        p.drawEllipse(QRectF(pill_x + 8, py + 7, 8, 8))
        # text
        p.setPen(Theme.TEXT)
        p.drawText(QRectF(pill_x + 22, py, pill_text_w - 22, pill_h),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   prov_label)

        # Status pill (LATE / IN PROGRESS)
        if self.is_late:
            status_text = "🔴 LATE • IN PROGRESS"
            status_bg   = Theme.get_color('RED', 220)
            status_fg   = Theme.CRUST
        else:
            status_text = ""
            status_bg   = QColor(0, 0, 0, 0)
            status_fg   = QColor(0, 0, 0, 0)

        if status_text:
            p.setFont(QFont("Inter, Arial", 8, QFont.Weight.Bold))
            fm2 = QFontMetrics(p.font())
            sw = fm2.horizontalAdvance(status_text) + 20
            sx = cx + CARD_W - 36 - sw  # 36 = close btn area
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(status_bg)
            p.drawRoundedRect(QRectF(sx, py, sw, pill_h), 11, 11)
            p.setPen(status_fg)
            p.drawText(QRectF(sx, py, sw, pill_h), Qt.AlignmentFlag.AlignCenter, status_text)

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
        sub_parts = []
        if self.time_str:
            sub_parts.append(f"🕙 {self.time_str}")
        if self.is_update_banner:
            sub_parts.append("⚡ Ready to download & install")
        elif "meet" in self.provider.lower() or "zoom" in self.provider.lower() or "teams" in self.provider.lower():
            sub_parts.append("🌐 Online Meeting")
        elif self.classroom:
            sub_parts.append(f"🏫 {self.classroom}")
        sub_text = "  •  ".join(sub_parts) if sub_parts else self.provider
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

        if self.is_update_banner:
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
        elif not self.has_real_url:
            # Got it styling (blue tint)
            g = QLinearGradient(jr.topLeft(), jr.topRight())
            if hover_join:
                g.setColorAt(0, Theme.BLUE)
                g.setColorAt(1, Theme.TEAL)
            else:
                g.setColorAt(0, Theme.TEAL)
                g.setColorAt(1, Theme.GREEN)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(g)
            p.drawRoundedRect(jr, 10, 10)
            p.setPen(Theme.CRUST)
            display_text = "✅ Got it"
        else:
            # JOIN styling (yellow/amber gradient, black text)
            g = QLinearGradient(jr.topLeft(), jr.topRight())
            if hover_join:
                g.setColorAt(0, Theme.YELLOW)
                g.setColorAt(1, Theme.PEACH)
            else:
                g.setColorAt(0, Theme.YELLOW)
                g.setColorAt(1, Theme.PEACH)
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

        if self.is_update_banner:
            sr = self._snooze_rect()
            hover_snz = self._hover == "snooze"
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(Theme.get_color('SURFACE1', 150) if hover_snz else Theme.SURFACE0)
            p.drawRoundedRect(sr, 10, 10)
            p.setPen(Theme.CRUST if hover_snz else Theme.SUBTEXT0)
            p.setFont(mf)
            p.drawText(sr, Qt.AlignmentFlag.AlignCenter, "✕ Later")
        else:
            # I'm Here (dark pill, greenish tint on hover)
            if self.has_maps_url:
                ar = self._arrive_rect()
                hover_arr = self._hover == "arrive"
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(Theme.get_color('GREEN', 180) if hover_arr else Theme.SURFACE0)
                p.drawRoundedRect(ar, 10, 10)
                p.setPen(Theme.CRUST if hover_arr else Theme.SUBTEXT1)
                p.setFont(mf)
                p.drawText(ar, Qt.AlignmentFlag.AlignCenter, "📍 I'm Here")

            # Snooze / Got it button
            sr = self._snooze_rect()
            hover_snz = self._hover == "snooze"
            p.setPen(Qt.PenStyle.NoPen)
            if self.reminder_stage == 0:
                p.setBrush(Theme.get_color('TEAL', 220) if hover_snz else Theme.MANTLE)
                p.drawRoundedRect(sr, 10, 10)
                p.setPen(Theme.CRUST if hover_snz else Theme.BLUE)
                p.setFont(mf)
                p.drawText(sr, Qt.AlignmentFlag.AlignCenter, "✅ Got it")
            else:
                p.setBrush(Theme.get_color('MAUVE', 180) if hover_snz else Theme.SURFACE0)
                p.drawRoundedRect(sr, 10, 10)
                p.setPen(Theme.CRUST if hover_snz else Theme.SUBTEXT1)
                p.setFont(mf)
                p.drawText(sr, Qt.AlignmentFlag.AlignCenter, "💤 Snooze 2m")

    # ── Tow cable ─────────────────────────────────────────────────────────────

    def _draw_cable(self, p: QPainter):
        pen = QPen(Theme.get_color('TEXT', 160), 1.4)
        p.setPen(pen)
        p.drawLine(
            int(CARD_X + CARD_W), int(CARD_Y + CARD_H // 2),
            int(PLANE_CX - 36),   int(PLANE_CY)
        )

    def _draw_plane(self, p: QPainter, px: float, py: float):
        # AppKit uses Y-up; Qt uses Y-down.
        # Flip the painter around py so all ported AppKit coordinates render correctly.
        p.save()
        p.translate(0.0, 2.0 * py)
        p.scale(1.0, -1.0)
        p.setPen(Qt.PenStyle.NoPen)
        renderer = get_pilot_renderer(self.pilot_type)
        renderer.draw_pilot(p, px, py, self.tick)
        p.restore()


    # ── Speech bubble ─────────────────────────────────────────────────────────

    def _draw_bubble(self, p: QPainter, px: float, py: float):
        is_late_q = self.is_late or "LATE" in self.quote_text or "RUN" in self.quote_text
        bg = Theme.get_color('RED', 230) if is_late_q else Theme.get_color('MANTLE', 220)

        f = QFont("Inter, Arial", 8)
        f.setWeight(QFont.Weight.ExtraBold)
        p.setFont(f)
        fm = p.fontMetrics()
        bw = max(180, fm.horizontalAdvance(self.quote_text) + 36)
        bh = 30
        bx = px - bw * 0.5
        by = py - 60

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(bx, by, bw, bh), 13, 13)

        # Tiny tail pointing down-right towards plane
        tail = QPainterPath()
        tail.moveTo(bx + bw * 0.65, by + bh)
        tail.lineTo(bx + bw * 0.65 + 8, by + bh + 8)
        tail.lineTo(bx + bw * 0.65 + 16, by + bh)
        tail.closeSubpath()
        p.drawPath(tail)

        p.setPen(Theme.TEXT)
        p.setFont(f)
        p.drawText(QRectF(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, self.quote_text)

    # ── Dismiss ───────────────────────────────────────────────────────────────

    def _dismiss(self):
        self.is_closing = True
        # Let _step handle the slide-up animation and call _finish_dismiss when done

    def _finish_dismiss(self):
        self._timer.stop()
        self.close()
        from .qt_banner import _active_banners
        if self in _active_banners:
            _active_banners.remove(self)
        app = QApplication.instance()
        if app and "--test" in sys.argv:
            app.quit()


