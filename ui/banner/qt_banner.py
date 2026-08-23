"""
PyQt6 Flying Mascot Banner for Ubuntu Linux.
Matches macOS QuakPit design:
  - Dark glass rounded card (provider pill, status pill, title, subtitle, 3-action buttons)
  - Mascot aircraft towing the card on a cable, entering from screen-right
  - Small window moved each frame via self.move() + QT_QPA_PLATFORM=xcb (XWayland)
  - Zero child widgets — everything drawn in paintEvent
"""
import sys
import os
import math
import webbrowser
from datetime import datetime
from typing import Dict, Any

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QPainterPath,
    QLinearGradient, QRadialGradient, QFontMetrics
)

# ── Pilot data ────────────────────────────────────────────────────────────────

PILOT_QUOTES = {
    "duck":     "QUAAK! 🚀 JOIN THE CALL!",
    "chef":     "🍕 DINNER TIME, LET'S GO!",
    "captain":  "✈️ CLEARED FOR TAKEOFF!",
    "owl":      "📚 LECTURE IS STARTING!",
    "gym":      "🏋️ GET TO THE GYM!",
    "driver":   "🚗 TIME TO LEAVE, GO GO GO!",
    "zen_duck": "🌸 BREATHE... YOU GOT THIS!",
}

PILOT_COLORS = {
    "duck":     QColor(250, 204, 21),
    "chef":     QColor(244, 63, 94),
    "captain":  QColor(56, 189, 248),
    "owl":      QColor(192, 132, 252),
    "gym":      QColor(248, 113, 113),
    "driver":   QColor(251, 191, 36),
    "zen_duck": QColor(45, 212, 191),
}

PROVIDER_DOTS = {
    "google meet": QColor(52, 211, 153),
    "zoom":        QColor(56, 189, 248),
    "teams":       QColor(99, 102, 241),
    "webex":       QColor(251, 191, 36),
    "meet":        QColor(52, 211, 153),
}

# ── Layout constants ──────────────────────────────────────────────────────────

CARD_W    = 500
CARD_H    = 148
CARD_R    = 18
CABLE_LEN = 60
PLANE_SPAN = 90       # horizontal span of plane drawing
WIN_W     = CARD_W + CABLE_LEN + PLANE_SPAN + 16
WIN_H     = 200       # height includes space for speech bubble above
CARD_X    = 0
CARD_Y    = 50        # card vertically centred inside WIN_H with room for bubble
PLANE_CX  = CARD_W + CABLE_LEN + PLANE_SPAN // 2   # plane centre inside window
PLANE_CY  = CARD_Y + CARD_H // 2

# Button layout
BTN_H     = 32
BTN_JOIN_W  = 170
BTN_SMALL_W = 100
BTN_Y     = CARD_Y + CARD_H - BTN_H - 12
BTN_X0    = CARD_X + 14
BTN_ARRIVE_X = BTN_X0 + BTN_JOIN_W + 8
BTN_SNOOZE_X = BTN_ARRIVE_X + BTN_SMALL_W + 8


class QtQuakPitFlyingBanner(QWidget):

    def __init__(self, event_data: Dict[str, Any]):
        super().__init__()
        self.event_data  = event_data
        self.pilot_type  = event_data.get("pilot_type", "duck")
        self.action_url  = event_data.get("action_url") or event_data.get("meeting_url")
        self.title       = str(event_data.get("title", "Upcoming Event"))
        self.provider    = str(event_data.get("provider", "Calendar"))
        self.btn_text    = event_data.get("action_btn_text", "🚀 JOIN MEETING")
        self.is_late     = bool(event_data.get("is_late", False))
        self.is_travel   = bool(event_data.get("is_travel", False))
        self.quote_text  = PILOT_QUOTES.get(self.pilot_type, "🚀 Meeting starting soon!")

        # Formatted time string
        st = event_data.get("start_time")
        self.time_str = st.strftime("At %H:%M") if hasattr(st, "strftime") else ""
        self.classroom = str(event_data.get("classroom") or "")

        # ── Screen ──
        screen = QApplication.primaryScreen()
        geo    = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        self.screen_w = geo.width()
        self.screen_x = geo.x()
        self.screen_y = geo.y()

        # ── Animation state — enter from LEFT, fly RIGHT ──
        self.win_x    = float(self.screen_x - WIN_W - 20)
        self.win_y    = self.screen_y + 14
        self.speed    = 3.8
        self.tick     = 0
        self.is_paused = False
        self._hover   = None   # "join" | "arrive" | "snooze" | "close"

        # ── Window setup ──
        self.setFixedSize(WIN_W, WIN_H)
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
        self.move(int(self.win_x), self.win_y)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(16)

    # ── Animation ─────────────────────────────────────────────────────────────

    def _step(self):
        self.tick += 1
        if not self.is_paused:
            self.win_x += self.speed
        bob = math.sin(self.tick * 0.035) * 5
        self.move(int(self.win_x), int(self.win_y + bob))
        if self.win_x > self.screen_x + self.screen_w + 20:
            self._dismiss()
        else:
            self.update()

    # ── Hit rects (window-local coords) ──────────────────────────────────────

    def _join_rect(self)   -> QRectF:
        return QRectF(BTN_X0, BTN_Y, BTN_JOIN_W, BTN_H)

    def _arrive_rect(self) -> QRectF:
        return QRectF(BTN_ARRIVE_X, BTN_Y, BTN_SMALL_W, BTN_H)

    def _snooze_rect(self) -> QRectF:
        return QRectF(BTN_SNOOZE_X, BTN_Y, BTN_SMALL_W, BTN_H)

    def _close_rect(self)  -> QRectF:
        s = 22
        return QRectF(CARD_X + CARD_W - s - 8, CARD_Y + 8, s, s)

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
        elif self._join_rect().contains(p) and self.action_url:
            webbrowser.open(self.action_url)
            self._dismiss()
        elif self._arrive_rect().contains(p):
            self._dismiss()
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
        self._draw_cable(p)
        self._draw_card(p)
        self._draw_plane(p, PLANE_CX, PLANE_CY)
        self._draw_bubble(p, PLANE_CX, PLANE_CY)
        p.end()

    # ── Card ──────────────────────────────────────────────────────────────────

    def _draw_card(self, p: QPainter):
        card = QRectF(CARD_X, CARD_Y, CARD_W, CARD_H)

        # ── Background: very dark glass, no shadow, no border ──
        p.setBrush(QColor(16, 18, 28, 245))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(card, CARD_R, CARD_R)

        # ── Row 1: Provider pill + Status pill + Close ──
        py = CARD_Y + 12

        # Provider pill
        prov_lower = self.provider.lower()
        dot_color = QColor(100, 200, 100)
        for k, c in PROVIDER_DOTS.items():
            if k in prov_lower:
                dot_color = c
                break
        prov_label = self.provider.upper()[:20]
        p.setFont(QFont("Inter, Arial", 9, QFont.Weight.ExtraBold))
        fm = QFontMetrics(p.font())
        pill_text_w = fm.horizontalAdvance(prov_label) + 24 + 12  # dot + text + padding
        pill_h = 22
        pill_x = CARD_X + 14

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(30, 34, 50, 255))
        p.drawRoundedRect(QRectF(pill_x, py, pill_text_w, pill_h), 11, 11)
        # dot
        p.setBrush(dot_color)
        p.drawEllipse(QRectF(pill_x + 8, py + 7, 8, 8))
        # text
        p.setPen(QColor(200, 210, 230))
        p.drawText(QRectF(pill_x + 22, py, pill_text_w - 22, pill_h),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   prov_label)

        # Status pill (LATE / IN PROGRESS)
        if self.is_late:
            status_text = "🔴 LATE • IN PROGRESS"
            status_bg   = QColor(180, 30, 30, 220)
            status_fg   = QColor(255, 200, 200)
        else:
            status_text = ""
            status_bg   = QColor(0, 0, 0, 0)
            status_fg   = QColor(0, 0, 0, 0)

        if status_text:
            p.setFont(QFont("Inter, Arial", 8, QFont.Weight.Bold))
            fm2 = QFontMetrics(p.font())
            sw = fm2.horizontalAdvance(status_text) + 20
            sx = CARD_X + CARD_W - 36 - sw  # 36 = close btn area
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(status_bg)
            p.drawRoundedRect(QRectF(sx, py, sw, pill_h), 11, 11)
            p.setPen(status_fg)
            p.drawText(QRectF(sx, py, sw, pill_h), Qt.AlignmentFlag.AlignCenter, status_text)

        # Close button ✕
        cr = self._close_rect()
        hover_close = self._hover == "close"
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(239, 68, 68, 200) if hover_close else QColor(255, 255, 255, 22))
        p.drawEllipse(cr)
        p.setPen(QColor(255, 255, 255, 220) if hover_close else QColor(150, 160, 180))
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        p.drawText(cr, Qt.AlignmentFlag.AlignCenter, "✕")

        # ── Row 2: Title ──
        p.setPen(QColor(248, 250, 252))
        tf = QFont("Inter, Arial", 15)
        tf.setWeight(QFont.Weight.Bold)
        p.setFont(tf)
        title_rect = QRectF(CARD_X + 14, CARD_Y + 40, CARD_W - 28, 26)
        fm_t = QFontMetrics(tf)
        elided = fm_t.elidedText(self.title, Qt.TextElideMode.ElideRight, int(CARD_W - 28))
        p.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)

        # ── Row 3: Subtitle ──
        sub_parts = []
        if self.time_str:
            sub_parts.append(f"🕙 {self.time_str}")
        if "meet" in self.provider.lower() or "zoom" in self.provider.lower() or "teams" in self.provider.lower():
            sub_parts.append("🌐 Online Meeting")
        elif self.classroom:
            sub_parts.append(f"🏫 {self.classroom}")
        sub_text = "  •  ".join(sub_parts) if sub_parts else self.provider
        p.setPen(QColor(148, 163, 184))
        sf = QFont("Inter, Arial", 10)
        p.setFont(sf)
        p.drawText(QRectF(CARD_X + 14, CARD_Y + 68, CARD_W - 28, 20),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, sub_text)

        # ── Row 4: Action Buttons ──
        # JOIN (yellow/amber gradient, black text)
        jr = self._join_rect()
        hover_join = self._hover == "join"
        g = QLinearGradient(jr.topLeft(), jr.topRight())
        if hover_join:
            g.setColorAt(0, QColor(253, 230, 70))
            g.setColorAt(1, QColor(251, 146, 60))
        else:
            g.setColorAt(0, QColor(234, 179, 8))
            g.setColorAt(1, QColor(245, 158, 11))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(jr, 10, 10)
        p.setPen(QColor(15, 15, 15))
        bf = QFont("Inter, Arial", 11)
        bf.setWeight(QFont.Weight.ExtraBold)
        p.setFont(bf)
        p.drawText(jr, Qt.AlignmentFlag.AlignCenter, self.btn_text)

        # I'm Here (dark pill, greenish tint on hover)
        ar = self._arrive_rect()
        hover_arr = self._hover == "arrive"
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(34, 197, 94, 180) if hover_arr else QColor(30, 34, 50, 255))
        p.drawRoundedRect(ar, 10, 10)
        p.setPen(QColor(255, 255, 255, 220) if hover_arr else QColor(180, 200, 230))
        mf = QFont("Inter, Arial", 10)
        mf.setWeight(QFont.Weight.Bold)
        p.setFont(mf)
        p.drawText(ar, Qt.AlignmentFlag.AlignCenter, "📍 I'm Here")

        # Snooze (dark pill, blue tint on hover)
        sr = self._snooze_rect()
        hover_snz = self._hover == "snooze"
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(99, 102, 241, 180) if hover_snz else QColor(30, 34, 50, 255))
        p.drawRoundedRect(sr, 10, 10)
        p.setPen(QColor(255, 255, 255, 220) if hover_snz else QColor(180, 200, 230))
        p.setFont(mf)
        p.drawText(sr, Qt.AlignmentFlag.AlignCenter, "💤 Snooze 2m")

    # ── Tow cable ─────────────────────────────────────────────────────────────

    def _draw_cable(self, p: QPainter):
        pen = QPen(QColor(180, 200, 240, 160), 1.4)
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
        if   self.pilot_type == "duck":     self._draw_duck(p, px, py)
        elif self.pilot_type == "chef":     self._draw_chef(p, px, py)
        elif self.pilot_type == "captain":  self._draw_captain(p, px, py)
        elif self.pilot_type == "owl":      self._draw_owl(p, px, py)
        elif self.pilot_type == "gym":      self._draw_gym(p, px, py)
        elif self.pilot_type == "driver":   self._draw_driver(p, px, py)
        elif self.pilot_type == "zen_duck": self._draw_zen_duck(p, px, py)
        else:                               self._draw_duck(p, px, py)
        p.restore()

    def _c(self, r, g, b, a=255) -> QColor:
        return QColor(r, g, b, a)

    def _propeller(self, p: QPainter, nx: float, ny: float):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(225, 240, 255, 64))
        p.drawEllipse(QRectF(nx - 4, ny - 18, 8, 36))
        angle = self.tick * 0.70
        dx = math.cos(angle) * 3.5
        dy = math.sin(angle) * 18.0
        pen = QPen(self._c(235, 242, 255, 230), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(nx + dx, ny - dy), QPointF(nx - dx, ny + dy))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(56, 66, 90));  p.drawEllipse(QRectF(nx - 3.5, ny - 4.5, 9, 9))
        p.setBrush(self._c(255, 255, 255, 200)); p.drawEllipse(QRectF(nx - 1, ny - 1.5, 3, 3))

    # ─── DUCK ─────────────────────────────────────────────────────────────────
    def _draw_duck(self, p: QPainter, px: float, py: float):
        # Tail fin red
        tail = QPainterPath()
        tail.moveTo(px-30,py-2); tail.lineTo(px-56,py+24); tail.lineTo(px-42,py-2); tail.closeSubpath()
        p.setBrush(self._c(230,56,51)); p.setPen(Qt.PenStyle.NoPen); p.drawPath(tail)
        deco = QPainterPath()
        deco.moveTo(px-38,py+3); deco.lineTo(px-48,py+16); deco.lineTo(px-44,py+16); deco.lineTo(px-35,py+3); deco.closeSubpath()
        p.setBrush(Qt.GlobalColor.white); p.drawPath(deco)
        # Cream vintage fuselage
        p.setBrush(self._c(250,240,209)); p.drawEllipse(QRectF(px-44,py-13,76,28))
        p.setBrush(self._c(225,199,158,153)); p.drawEllipse(QRectF(px-42,py-15,72,16))
        stripe = QPainterPath()
        stripe.moveTo(px-38,py-2); stripe.lineTo(px+24,py-2); stripe.lineTo(px+22,py-6); stripe.lineTo(px-36,py-6); stripe.closeSubpath()
        p.setBrush(self._c(225,51,46)); p.drawPath(stripe)
        p.setPen(QPen(self._c(89,64,38,217), 1.4)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px-44,py-13,76,28)); p.setPen(Qt.PenStyle.NoPen)
        # Cockpit + windshield
        p.setBrush(self._c(38,46,64)); p.drawEllipse(QRectF(px-14,py,26,16))
        glass = QPainterPath(); glass.moveTo(px+10,py+1)
        glass.cubicTo(px+8,py+12, px+2,py+16, px-2,py+17); glass.lineTo(px-8,py+1); glass.closeSubpath()
        p.setBrush(self._c(166,225,250,191)); p.drawPath(glass)
        p.setPen(QPen(self._c(255,255,255,229), 1.2)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(glass)
        p.setPen(Qt.PenStyle.NoPen)
        # Animated scarf
        w1 = math.sin(self.tick*0.28)*5.0; w2 = math.sin(self.tick*0.28+1.2)*6.5
        scarf = QPainterPath(); scarf.moveTo(px-8,py+5)
        scarf.cubicTo(px-15,py+4+w1*0.5, px-22,py+10+w1, px-28,py+7+w1)
        scarf.cubicTo(px-34,py+5+w1, px-40,py+8+w2, px-46,py+4+w2)
        scarf.lineTo(px-45,py-1+w2)
        scarf.cubicTo(px-38,py+3+w2, px-32,py+w1, px-26,py+2+w1); scarf.closeSubpath()
        p.setBrush(self._c(235,46,46)); p.drawPath(scarf)
        p.setPen(QPen(self._c(255,217,64), 1.6))
        p.drawLine(QPointF(px-46,py+4+w2),QPointF(px-49,py+3+w2))
        p.drawLine(QPointF(px-45,py+1.5+w2),QPointF(px-48,py+0.5+w2)); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(217,38,38)); p.drawEllipse(QRectF(px-9,py+2,11,7))
        # Duck head + blush
        p.setBrush(self._c(235,166,38)); p.drawEllipse(QRectF(px-7,py+2,19,18))
        p.setBrush(self._c(255,209,61)); p.drawEllipse(QRectF(px-8,py+3,20,20))
        p.setBrush(self._c(255,235,128,178)); p.drawEllipse(QRectF(px-5,py+9,14,13))
        p.setBrush(self._c(255,107,107,115)); p.drawEllipse(QRectF(px-3,py+5,7,5))
        # Eye + catchlights
        p.setBrush(self._c(26,26,31)); p.drawEllipse(QRectF(px+2.5,py+12,5.0,5.5))
        p.setBrush(Qt.GlobalColor.white); p.drawEllipse(QRectF(px+4.2,py+14.2,2.2,2.2)); p.drawEllipse(QRectF(px+3.2,py+12.8,1.0,1.0))
        # Beak 3D
        beak = QPainterPath(); beak.moveTo(px+5,py+12)
        beak.cubicTo(px+10,py+13, px+15,py+12, px+18,py+9.5)
        beak.cubicTo(px+15,py+7, px+10,py+6, px+5,py+5.5); beak.closeSubpath()
        p.setBrush(self._c(255,122,5)); p.drawPath(beak)
        p.setPen(QPen(self._c(255,184,64,217), 1.2))
        p.drawLine(QPointF(px+7,py+11),QPointF(px+14,py+9.5)); p.setPen(Qt.PenStyle.NoPen)
        # Leather cap
        cap = QPainterPath(); cap.moveTo(px-8,py+12)
        cap.cubicTo(px-6,py+23, px+2,py+24, px+6,py+22); cap.lineTo(px+6,py+18)
        cap.cubicTo(px,py+18, px-5,py+14, px-8,py+12); cap.closeSubpath()
        p.setBrush(self._c(97,56,31)); p.drawPath(cap)
        p.setBrush(self._c(64,38,20)); p.drawRect(QRectF(px-8,py+12.5,18,3.5))
        # Gold goggles
        p.setPen(QPen(self._c(235,199,64), 2.4)); p.setBrush(self._c(128,217,250,217))
        p.drawEllipse(QRectF(px-1.5,py+10,12,11))
        p.setPen(QPen(self._c(255,255,255,217), 1.4))
        p.drawLine(QPointF(px+3,py+18),QPointF(px+7,py+13)); p.setPen(Qt.PenStyle.NoPen)
        # Wing red with white trim
        wing = QPainterPath()
        wing.moveTo(px-18,py-2); wing.lineTo(px+18,py-2); wing.lineTo(px+8,py-24); wing.lineTo(px-12,py-24); wing.closeSubpath()
        p.setBrush(self._c(230,56,51)); p.drawPath(wing)
        p.setPen(QPen(Qt.GlobalColor.white, 2.0))
        p.drawLine(QPointF(px-12,py-24),QPointF(px+8,py-24)); p.setPen(Qt.PenStyle.NoPen)
        self._propeller(p, px+32.0, py+2.0)

    # ─── CHEF ─────────────────────────────────────────────────────────────────
    def _draw_chef(self, p: QPainter, px: float, py: float):
        p.setBrush(self._c(255,148,122)); p.drawEllipse(QRectF(px-44,py-13,76,28))
        p.setPen(QPen(self._c(102,51,38,217), 1.4)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px-44,py-13,76,28)); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(255,209,61)); p.drawEllipse(QRectF(px-8,py+2,19,19))
        p.setBrush(self._c(255,107,107,115)); p.drawEllipse(QRectF(px-3,py+4,7,5))
        p.setBrush(self._c(26,26,31)); p.drawEllipse(QRectF(px+2,py+10.5,4.5,5.0))
        p.setBrush(Qt.GlobalColor.white); p.drawEllipse(QRectF(px+3.8,py+12.5,2.0,2.0))
        beak = QPainterPath(); beak.moveTo(px+4,py+11)
        beak.cubicTo(px+9,py+12, px+14,py+11, px+17,py+8.5)
        beak.cubicTo(px+14,py+6, px+9,py+5.5, px+4,py+5.0); beak.closeSubpath()
        p.setBrush(self._c(255,122,5)); p.drawPath(beak)
        # Bandana
        p.setBrush(self._c(235,46,46)); p.drawEllipse(QRectF(px-6,py-2,14,8))
        p.setBrush(Qt.GlobalColor.white); p.drawEllipse(QRectF(px-3,py,2.2,2.2)); p.drawEllipse(QRectF(px+3,py,2.2,2.2))
        b_wave = math.sin(self.tick*0.3)*4.0
        bt = QPainterPath(); bt.moveTo(px-6,py+1); bt.lineTo(px-20,py+2+b_wave); bt.lineTo(px-6,py-3); bt.closeSubpath()
        p.setBrush(self._c(235,46,46)); p.drawPath(bt)
        # Toque blanche
        p.setBrush(Qt.GlobalColor.white)
        p.drawRoundedRect(QRectF(px-6,py+14,16,6), 2,2)
        p.drawEllipse(QRectF(px-12,py+17,14,15)); p.drawEllipse(QRectF(px-3,py+19,15,16)); p.drawEllipse(QRectF(px+4,py+16,12,14))
        p.setPen(QPen(self._c(209,217,235), 1.3))
        p.drawLine(QPointF(px-4,py+17),QPointF(px-4,py+30)); p.drawLine(QPointF(px+4,py+17),QPointF(px+4,py+30))
        p.setPen(Qt.PenStyle.NoPen)
        # Silver tray + pizza
        p.setBrush(self._c(225,235,250)); p.drawEllipse(QRectF(px-30,py-20,26,8))
        pizza = QPainterPath(); pizza.moveTo(px-28,py-18); pizza.lineTo(px-9,py-14); pizza.lineTo(px-15,py-7); pizza.closeSubpath()
        p.setBrush(self._c(255,209,51)); p.drawPath(pizza)
        p.setBrush(self._c(230,51,38)); p.drawEllipse(QRectF(px-21,py-15,4.5,4.5)); p.drawEllipse(QRectF(px-14,py-13,3.5,3.5))
        steam_y = math.sin(self.tick*0.15)*3.0
        p.setPen(QPen(self._c(242,242,255,166), 1.4))
        steam = QPainterPath(); steam.moveTo(px-17,py-5)
        steam.cubicTo(px-22,py+steam_y*0.5, px-10,py+3+steam_y, px-14,py+6+steam_y)
        p.drawPath(steam); p.setPen(Qt.PenStyle.NoPen)
        wing = QPainterPath()
        wing.moveTo(px-16,py-2); wing.lineTo(px+16,py-2); wing.lineTo(px+6,py-24); wing.lineTo(px-10,py-24); wing.closeSubpath()
        p.setBrush(self._c(245,107,89)); p.drawPath(wing)
        self._propeller(p, px+32.0, py+2.0)

    # ─── CAPTAIN ──────────────────────────────────────────────────────────────
    def _draw_captain(self, p: QPainter, px: float, py: float):
        tail = QPainterPath()
        tail.moveTo(px-38,py); tail.lineTo(px-66,py+28); tail.lineTo(px-48,py); tail.closeSubpath()
        p.setBrush(self._c(26,56,122)); p.drawPath(tail)
        p.setBrush(Qt.GlobalColor.white); p.drawEllipse(QRectF(px-48,py-12,88,26))
        p.setPen(QPen(self._c(51,77,115), 1.4)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px-48,py-12,88,26)); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(31,82,166)); p.drawRect(QRectF(px-36,py-2,62,4))
        p.setBrush(self._c(217,240,255))
        for i in range(5): p.drawEllipse(QRectF(px-28+i*8,py-1,4.5,3.5))
        p.setBrush(self._c(31,46,82,242)); p.drawEllipse(QRectF(px+20,py+2,17,9))
        p.setBrush(self._c(255,209,61)); p.drawEllipse(QRectF(px-4,py+2,18,18))
        p.setBrush(self._c(26,31,46,242)); p.drawEllipse(QRectF(px+3,py+7,7,6))
        p.setPen(QPen(self._c(255,217,64), 1.6)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawEllipse(QRectF(px+3,py+7,7,6)); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(26,38,89)); p.drawRect(QRectF(px-3,py+14,18,6))
        p.setBrush(Qt.GlobalColor.white); p.drawEllipse(QRectF(px-4,py+16,20,7))
        p.setBrush(self._c(250,217,64)); p.drawEllipse(QRectF(px+2,py+15,6,5))
        wing = QPainterPath()
        wing.moveTo(px-14,py-2); wing.lineTo(px+18,py-2); wing.lineTo(px+4,py-26); wing.lineTo(px-8,py-26); wing.closeSubpath()
        p.setBrush(self._c(209,222,242)); p.drawPath(wing)
        p.setBrush(self._c(71,82,107)); p.drawRoundedRect(QRectF(px-4,py-22,20,9), 3.5,3.5)
        p.setBrush(self._c(166,191,230)); p.drawEllipse(QRectF(px+12,py-21,3.5,7))
        self._propeller(p, px+42.0, py+2.0)

    # ─── OWL ──────────────────────────────────────────────────────────────────
    def _draw_owl(self, p: QPainter, px: float, py: float):
        p.setBrush(self._c(112,71,166)); p.drawEllipse(QRectF(px-44,py-13,76,28))
        p.setBrush(self._c(179,133,102)); p.drawEllipse(QRectF(px-8,py+2,21,21))
        p.setBrush(self._c(245,240,224)); p.drawEllipse(QRectF(px-4,py+7,8.5,8.5)); p.drawEllipse(QRectF(px+5.5,py+7,8.5,8.5))
        p.setBrush(Qt.GlobalColor.black); p.drawEllipse(QRectF(px-2,py+9,4.5,4.5)); p.drawEllipse(QRectF(px+7.5,py+9,4.5,4.5))
        p.setBrush(Qt.GlobalColor.white); p.drawEllipse(QRectF(px-0.8,py+11,1.6,1.6)); p.drawEllipse(QRectF(px+8.7,py+11,1.6,1.6))
        p.setPen(QPen(self._c(255,217,64), 1.6)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px-4.5,py+6.5,9.5,9.5)); p.drawEllipse(QRectF(px+5.0,py+6.5,9.5,9.5)); p.setPen(Qt.PenStyle.NoPen)
        beak = QPainterPath(); beak.moveTo(px+3,py+9.5); beak.lineTo(px+8,py+6.5); beak.lineTo(px+3,py+3.5); beak.closeSubpath()
        p.setBrush(self._c(242,140,26)); p.drawPath(beak)
        grad = QPainterPath(); grad.moveTo(px+2,py+27); grad.lineTo(px+16,py+20); grad.lineTo(px+2,py+15); grad.lineTo(px-12,py+20); grad.closeSubpath()
        p.setBrush(self._c(31,31,41)); p.drawPath(grad)
        tassel_wave = math.sin(self.tick*0.2)*3.0
        p.setBrush(self._c(255,217,51)); p.drawEllipse(QRectF(px+1,py+20,3,3))
        p.setPen(QPen(self._c(255,217,51), 1.6))
        p.drawLine(QPointF(px+2,py+21),QPointF(px-7+tassel_wave,py+13)); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(245,240,217)); p.drawRoundedRect(QRectF(px-24,py-19,18,8), 2.5,2.5)
        p.setBrush(self._c(230,46,46)); p.drawRect(QRectF(px-16,py-19,3.5,8))
        wing = QPainterPath()
        wing.moveTo(px-16,py-2); wing.lineTo(px+16,py-2); wing.lineTo(px+6,py-24); wing.lineTo(px-10,py-24); wing.closeSubpath()
        p.setBrush(self._c(194,133,245)); p.drawPath(wing)
        self._propeller(p, px+32.0, py+2.0)

    # ─── GYM ──────────────────────────────────────────────────────────────────
    def _draw_gym(self, p: QPainter, px: float, py: float):
        p.setBrush(self._c(255,87,38)); p.drawEllipse(QRectF(px-44,py-13,76,28))
        p.setBrush(self._c(255,230,26)); p.drawRect(QRectF(px-40,py-1,68,3.5))
        p.setBrush(Qt.GlobalColor.white); p.drawEllipse(QRectF(px-28,py-9,16,16))
        p.setBrush(self._c(38,38,51))
        p.drawRoundedRect(QRectF(px-26,py-7,2.5,12), 1,1); p.drawRect(QRectF(px-24,py-2,8,2)); p.drawRoundedRect(QRectF(px-16,py-7,2.5,12), 1,1)
        p.setBrush(self._c(255,217,46)); p.drawEllipse(QRectF(px-6,py+3,19,19))
        p.setBrush(self._c(235,38,51)); p.drawRoundedRect(QRectF(px-7,py+12,21,6), 2,2)
        tail = QPainterPath(); tail.moveTo(px-7,py+14); tail.lineTo(px-15,py+18); tail.lineTo(px-14,py+12); tail.closeSubpath()
        p.drawPath(tail)
        p.setBrush(Qt.GlobalColor.white); p.drawEllipse(QRectF(px+4,py+7,6,6))
        p.setBrush(Qt.GlobalColor.black); p.drawEllipse(QRectF(px+6,py+8.5,3.5,3.5))
        beak = QPainterPath(); beak.moveTo(px+10,py+5); beak.lineTo(px+22,py+4); beak.lineTo(px+10,py+10); beak.closeSubpath()
        p.setBrush(self._c(255,128,13)); p.drawPath(beak)
        wing = QPainterPath()
        wing.moveTo(px-16,py-2); wing.lineTo(px+16,py-2); wing.lineTo(px+8,py-24); wing.lineTo(px-8,py-24); wing.closeSubpath()
        p.setBrush(self._c(230,51,38)); p.drawPath(wing)
        p.setBrush(self._c(255,235,64)); p.drawRect(QRectF(px-8,py-12,16,2.5))
        self._propeller(p, px+32.0, py+2.0)

    # ─── DRIVER ───────────────────────────────────────────────────────────────
    def _draw_driver(self, p: QPainter, px: float, py: float):
        p.setBrush(self._c(38,204,138)); p.drawEllipse(QRectF(px-44,py-13,76,28))
        p.setBrush(Qt.GlobalColor.white)
        p.drawRect(QRectF(px-40,py+1,68,3)); p.drawRect(QRectF(px-40,py-6,68,3))
        p.drawEllipse(QRectF(px-28,py-8,15,15))
        p.setPen(Qt.GlobalColor.black)
        f = QFont("Arial", 9); f.setWeight(QFont.Weight.Bold); p.setFont(f)
        # Un-flip Y around the text centre so "1" appears right-side-up
        tx, ty = px - 19, py - 1   # centre of the roundel
        p.save(); p.translate(0, 2*ty); p.scale(1, -1)
        p.drawText(QRectF(px-24, py-7, 10, 12), Qt.AlignmentFlag.AlignCenter, "1")
        p.restore()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(235,51,51)); p.drawEllipse(QRectF(px-8,py+3,20,20))
        p.setBrush(self._c(20,26,38)); p.drawRoundedRect(QRectF(px-1,py+8,14,9), 3.5,3.5)
        p.setBrush(self._c(102,230,255,217)); p.drawRect(QRectF(px+2,py+12,8,2.5))
        wing = QPainterPath()
        wing.moveTo(px-16,py-2); wing.lineTo(px+16,py-2); wing.lineTo(px+6,py-24); wing.lineTo(px-10,py-24); wing.closeSubpath()
        p.setBrush(self._c(250,217,56)); p.drawPath(wing)
        self._propeller(p, px+32.0, py+2.0)

    # ─── ZEN DUCK ─────────────────────────────────────────────────────────────
    def _draw_zen_duck(self, p: QPainter, px: float, py: float):
        p.setBrush(self._c(107,224,214)); p.drawEllipse(QRectF(px-44,py-13,76,28))
        p.setBrush(self._c(255,214,82)); p.drawEllipse(QRectF(px-8,py+2,19,19))
        p.setBrush(self._c(255,128,153,128)); p.drawEllipse(QRectF(px-3,py+4,7,5))
        pen = QPen(self._c(64,51,46), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        eye = QPainterPath(); eye.moveTo(px+1,py+10.5)
        eye.cubicTo(px+3,py+13, px+5.5,py+13, px+7.5,py+10.5); p.drawPath(eye)
        p.setPen(Qt.PenStyle.NoPen)
        beak = QPainterPath(); beak.moveTo(px+4,py+11); beak.lineTo(px+15,py+8.5); beak.lineTo(px+4,py+5.5); beak.closeSubpath()
        p.setBrush(self._c(255,133,26)); p.drawPath(beak)
        # Lotus 🌸
        p.setBrush(self._c(255,158,199))
        p.drawEllipse(QRectF(px-10,py+14,7,7)); p.drawEllipse(QRectF(px-5,py+18,7,7)); p.drawEllipse(QRectF(px,py+14,7,7))
        p.setBrush(self._c(255,230,77)); p.drawEllipse(QRectF(px-5,py+14,5,5))
        wing = QPainterPath()
        wing.moveTo(px-16,py-2); wing.lineTo(px+16,py-2); wing.lineTo(px+6,py-24); wing.lineTo(px-10,py-24); wing.closeSubpath()
        p.setBrush(self._c(158,240,230)); p.drawPath(wing)
        self._propeller(p, px+32.0, py+2.0)


    # ── Speech bubble ─────────────────────────────────────────────────────────

    def _draw_bubble(self, p: QPainter, px: float, py: float):
        is_late_q = self.is_late or "LATE" in self.quote_text or "RUN" in self.quote_text
        bg = QColor(200, 30, 30, 230) if is_late_q else QColor(16, 18, 28, 220)

        bw, bh = 180, 26
        bx = px - 90
        by = py - 56

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

        p.setPen(QColor(255, 255, 255))
        f = QFont("Inter, Arial", 8)
        f.setWeight(QFont.Weight.ExtraBold)
        p.setFont(f)
        p.drawText(QRectF(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, self.quote_text)

    # ── Dismiss ───────────────────────────────────────────────────────────────

    def _dismiss(self):
        self._timer.stop()
        self.close()
        if self in _active_banners:
            _active_banners.remove(self)
        app = QApplication.instance()
        if app and "--test" in sys.argv:
            app.quit()


_active_banners = []


# ── Public entry point ────────────────────────────────────────────────────────

def show_qt_banner(event_data: Dict[str, Any]) -> None:
    """Launch flying banner. Forces XCB so self.move() works on Wayland."""
    # Wayland blocks window positioning — use XWayland instead
    if "WAYLAND_DISPLAY" in os.environ or os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    app = QApplication.instance()
    standalone = app is None
    if standalone:
        app = QApplication(sys.argv)

    banner = QtQuakPitFlyingBanner(event_data)
    _active_banners.append(banner)
    banner.show()

    if standalone or "--test" in sys.argv:
        app.exec()

