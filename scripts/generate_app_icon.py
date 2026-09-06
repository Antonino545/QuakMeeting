"""
High-Fidelity Application Icon Generator for QuakMeeting.
Supports cross-platform rendering (PyQt6 / QPainter on Linux and macOS, with AppKit fallback).
Generates a smooth G2 continuous-curvature squircle with crisp defined edges and no shadow fringe.
"""
import math
import os
import sys

def create_superellipse_path(QPainterPath, cx: float, cy: float, rx: float, ry: float, n: float = 4.6, steps: int = 720):
    """Generates a mathematically continuous G2 squircle / superellipse curve path."""
    path = QPainterPath()
    for i in range(steps + 1):
        theta = 2.0 * math.pi * i / steps
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        x = cx + rx * (1.0 if cos_t >= 0 else -1.0) * (abs(cos_t) ** (2.0 / n))
        y = cy + ry * (1.0 if sin_t >= 0 else -1.0) * (abs(sin_t) ** (2.0 / n))
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()
    return path


def create_app_icon_qt(output_path="assets/icon.png", size=1024):
    from PyQt6.QtCore import Qt, QRectF, QPointF
    from PyQt6.QtGui import (
        QImage, QPainter, QPainterPath, QColor, QLinearGradient, QPen, QBrush
    )

    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    s = size / 512.0
    margin = size * 0.055
    w_sq = size - 2 * margin
    rx = w_sq / 2.0
    ry = w_sq / 2.0
    cx = size / 2.0
    cy = size / 2.0
    bg_path = create_superellipse_path(QPainterPath, cx, cy, rx, ry, n=4.6, steps=720)

    # 1. Sky Gradient Background
    grad = QLinearGradient(cx, margin, cx, size - margin)
    grad.setColorAt(0.0, QColor(38, 115, 224))   # vibrant sky blue (0.15, 0.45, 0.88)
    grad.setColorAt(1.0, QColor(13, 46, 107))    # deep navy blue (0.05, 0.18, 0.42)
    p.fillPath(bg_path, QBrush(grad))

    # Clean, crisp boundary hairline stroke (defines boundary against dark/light wallpapers)
    edge_pen = QPen(QColor(10, 30, 70, 160), 1.0 * s)
    p.strokePath(bg_path, edge_pen)

    # Inner Rim Highlight (strictly clipped inside the squircle)
    p.save()
    p.setClipPath(bg_path)

    inner_pen = QPen(QColor(255, 255, 255, 65), 2.2 * s)
    p.strokePath(bg_path, inner_pen)

    # Convert coordinates to match AppKit canvas convention (y=0 bottom, y=size top)
    p.translate(0, size)
    p.scale(1, -1)

    # 2. Clouds in Background
    cloud_col = QColor(255, 255, 255, 38)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(cloud_col))
    p.drawEllipse(QRectF(size * 0.15, size * 0.25, size * 0.35, size * 0.20))
    p.drawEllipse(QRectF(size * 0.45, size * 0.30, size * 0.40, size * 0.22))

    # 3. Aviator Duck Mascot (Center)
    center_x = size * 0.50
    center_y = size * 0.48

    # Timone di Coda (Tail Rudder)
    p.setBrush(QBrush(QColor(int(0.92 * 255), int(0.38 * 255), int(0.32 * 255))))
    tail = QPainterPath()
    tail.moveTo(center_x - 110 * s, center_y)
    tail.lineTo(center_x - 170 * s, center_y + 70 * s)
    tail.lineTo(center_x - 145 * s, center_y)
    tail.closeSubpath()
    p.fillPath(tail, p.brush())

    # Fusoliera Vintage Dorata / Avorio
    p.setBrush(QBrush(QColor(int(0.98 * 255), int(0.88 * 255), int(0.65 * 255))))
    body_pen = QPen(QColor(int(0.35 * 255), int(0.25 * 255), int(0.15 * 255)), 4.0 * s)
    p.setPen(body_pen)
    body_rect = QRectF(center_x - 130 * s, center_y - 40 * s, 230 * s, 90 * s)
    p.drawEllipse(body_rect)

    # Striscia Rossa Racing sulla Fiancata
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(int(0.90 * 255), int(0.25 * 255), int(0.22 * 255))))
    p.drawRoundedRect(QRectF(center_x - 105 * s, center_y - 8 * s, 175 * s, 16 * s), 4 * s, 4 * s)

    # Parabrezza Cockpit Lucido
    p.setBrush(QBrush(QColor(int(0.65 * 255), int(0.88 * 255), int(0.98 * 255), int(0.85 * 255))))
    p.drawEllipse(QRectF(center_x - 40 * s, center_y - 5 * s, 90 * s, 70 * s))

    # Testa Papero Dorato 🦆
    p.setBrush(QBrush(QColor(int(1.0 * 255), int(0.82 * 255), int(0.28 * 255))))
    p.drawEllipse(QRectF(center_x - 25 * s, center_y + 5 * s, 60 * s, 60 * s))

    # Occhio con punto luce
    p.setBrush(QBrush(QColor(0, 0, 0)))
    p.drawEllipse(QRectF(center_x + 8 * s, center_y + 35 * s, 13 * s, 13 * s))
    p.setBrush(QBrush(QColor(255, 255, 255)))
    p.drawEllipse(QRectF(center_x + 13 * s, center_y + 40 * s, 5 * s, 5 * s))

    # Becco d Anatra Arancione Brillante
    p.setBrush(QBrush(QColor(int(1.0 * 255), int(0.48 * 255), 0)))
    beak = QPainterPath()
    beak.moveTo(center_x + 18 * s, center_y + 36 * s)
    beak.lineTo(center_x + 55 * s, center_y + 26 * s)
    beak.lineTo(center_x + 18 * s, center_y + 16 * s)
    beak.closeSubpath()
    p.fillPath(beak, p.brush())

    # Occhialoni da Aviatore con riflesso azzurro
    p.setBrush(QBrush(QColor(int(0.35 * 255), int(0.25 * 255), int(0.18 * 255))))
    p.drawRect(QRectF(center_x - 25 * s, center_y + 28 * s, 60 * s, 10 * s))

    goggle_rect = QRectF(center_x - 5 * s, center_y + 22 * s, 36 * s, 34 * s)
    p.setPen(QPen(QColor(int(0.90 * 255), int(0.75 * 255), int(0.35 * 255)), 6.0 * s))
    p.setBrush(QBrush(QColor(int(0.55 * 255), int(0.88 * 255), int(0.98 * 255), int(0.75 * 255))))
    p.drawEllipse(goggle_rect)

    # Ala Inferiore Vintage
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(int(0.92 * 255), int(0.38 * 255), int(0.32 * 255))))
    wing = QPainterPath()
    wing.moveTo(center_x - 50 * s, center_y - 8 * s)
    wing.lineTo(center_x + 50 * s, center_y - 8 * s)
    wing.lineTo(center_x + 20 * s, center_y - 75 * s)
    wing.lineTo(center_x - 30 * s, center_y - 75 * s)
    wing.closeSubpath()
    p.fillPath(wing, p.brush())

    # Ogiva Anteriore
    p.setBrush(QBrush(QColor(int(0.22 * 255), int(0.25 * 255), int(0.32 * 255))))
    p.drawEllipse(QRectF(center_x + 95 * s, center_y - 12 * s, 26 * s, 26 * s))

    # Elica con Motion Blur Rotante
    prop_pen = QPen(QColor(int(0.90 * 255), int(0.94 * 255), 255, int(0.75 * 255)), 8.0 * s)
    prop_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(prop_pen)
    p.drawLine(QPointF(center_x + 108 * s, center_y - 60 * s), QPointF(center_x + 108 * s, center_y + 60 * s))

    p.restore()
    p.end()

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path)
    print(f"✅ Icon successfully generated: {output_path} ({size}x{size})")


def export_multi_resolution(master_path="assets/icon.png", target_dir=None, sizes=(512, 256, 128, 64, 48, 32, 24, 16)):
    """Exports multi-resolution PNGs using high-quality Lanczos resampling."""
    try:
        from PIL import Image
    except ImportError:
        print("ℹ️ PIL not available for multi-resolution export, skipping.")
        return

    if not os.path.exists(master_path):
        return

    img = Image.open(master_path)
    if target_dir is None:
        target_dir = os.path.dirname(os.path.abspath(master_path))

    for sz in sizes:
        dest_path = os.path.join(target_dir, f"icon_{sz}x{sz}.png")
        resized = img.resize((sz, sz), Image.Resampling.LANCZOS)
        resized.save(dest_path)
        print(f"  📦 Generated {dest_path}")


def create_app_icon(output_path="assets/icon.png", size=1024):
    try:
        create_app_icon_qt(output_path, size)
    except ImportError:
        # Fallback to AppKit on macOS if PyQt6 is not installed
        import AppKit
        s = size / 512.0
        image = AppKit.NSImage.alloc().initWithSize_(AppKit.NSMakeSize(size, size))
        image.lockFocus()

        margin = size * 0.055
        icon_rect = AppKit.NSMakeRect(margin, margin, size - 2 * margin, size - 2 * margin)
        corner_radius = size * 0.22
        bg_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            icon_rect, corner_radius, corner_radius
        )

        c_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.45, 0.88, 1.0)
        c_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.05, 0.18, 0.42, 1.0)
        grad = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(c_top, c_bot)
        grad.drawInBezierPath_angle_(bg_path, 270.0)

        # Hairline outer edge
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.04, 0.12, 0.28, 0.65).set()
        bg_path.setLineWidth_(1.0 * s)
        bg_path.stroke()

        ctx = AppKit.NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()
        bg_path.addClip()

        AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.25).set()
        bg_path.setLineWidth_(2.2 * s)
        bg_path.stroke()

        ctx.restoreGraphicsState()
        image.unlockFocus()

        tiff_data = image.TIFFRepresentation()
        bitmap = AppKit.NSBitmapImageRep.imageRepsWithData_(tiff_data)[0]
        png_data = bitmap.representationUsingType_properties_(AppKit.NSBitmapImageFileTypePNG, None)
        png_data.writeToFile_atomically_(output_path, True)
        print(f"✅ Icon successfully generated (AppKit fallback): {output_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/icon.png"
    create_app_icon(out, 1024)
