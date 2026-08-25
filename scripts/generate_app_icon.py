import AppKit
import math
import os

def create_app_icon(output_path="assets/icon.png", size=512):
    image = AppKit.NSImage.alloc().initWithSize_(AppKit.NSMakeSize(size, size))
    image.lockFocus()

    # 1. Background Squircle (macOS Big Sur+ Continuous Curve App Icon Shape)
    margin = size * 0.08
    icon_rect = AppKit.NSMakeRect(margin, margin, size - 2 * margin, size - 2 * margin)
    corner_radius = size * 0.22
    bg_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
        icon_rect, corner_radius, corner_radius
    )

    # Shadow for Squircle
    shadow = AppKit.NSShadow.alloc().init()
    shadow.setShadowColor_(AppKit.NSColor.colorWithWhite_alpha_(0.0, 0.35))
    shadow.setShadowOffset_(AppKit.NSMakeSize(0.0, -size * 0.04))
    shadow.setShadowBlurRadius_(size * 0.08)
    shadow.set()

    # Sky Gradient Background
    c_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.45, 0.88, 1.0)
    c_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.05, 0.18, 0.42, 1.0)
    grad = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(c_top, c_bot)
    grad.drawInBezierPath_angle_(bg_path, 270.0)

    # Remove shadow for inner graphics
    no_shadow = AppKit.NSShadow.alloc().init()
    no_shadow.set()

    # Inner Rim Highlight
    hi_rect = AppKit.NSMakeRect(icon_rect.origin.x + 2, icon_rect.origin.y + icon_rect.size.height - 4, icon_rect.size.width - 4, 3)
    AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.28).set()
    AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(hi_rect, 1.5, 1.5).fill()

    # 2. Clouds in Background
    cloud_col = AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.15)
    cloud_col.set()
    AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(size * 0.15, size * 0.25, size * 0.35, size * 0.20)).fill()
    AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(size * 0.45, size * 0.30, size * 0.40, size * 0.22)).fill()

    # 3. Aviator Duck Mascot (Center)
    center_x = size * 0.50
    center_y = size * 0.48
    s = size / 512.0

    # Timone di Coda
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.38, 0.32, 1.0).set()
    tail = AppKit.NSBezierPath.bezierPath()
    tail.moveToPoint_(AppKit.NSMakePoint(center_x - 110 * s, center_y))
    tail.lineToPoint_(AppKit.NSMakePoint(center_x - 170 * s, center_y + 70 * s))
    tail.lineToPoint_(AppKit.NSMakePoint(center_x - 145 * s, center_y))
    tail.closePath()
    tail.fill()

    # Fusoliera Vintage Dorata / Avorio
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.88, 0.65, 1.0).set()
    body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
        AppKit.NSMakeRect(center_x - 130 * s, center_y - 40 * s, 230 * s, 90 * s)
    )
    body.fill()
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.35, 0.25, 0.15, 1.0).set()
    body.setLineWidth_(4.0 * s)
    body.stroke()

    # Striscia Rossa Racing sulla Fiancata
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.25, 0.22, 1.0).set()
    AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
        AppKit.NSMakeRect(center_x - 105 * s, center_y - 8 * s, 175 * s, 16 * s), 4 * s, 4 * s
    ).fill()

    # Parabrezza Cockpit Lucido
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.65, 0.88, 0.98, 0.85).set()
    AppKit.NSBezierPath.bezierPathWithOvalInRect_(
        AppKit.NSMakeRect(center_x - 40 * s, center_y - 5 * s, 90 * s, 70 * s)
    ).fill()

    # Testa Papero Dorato 🦆
    AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.28, 1.0).set()
    AppKit.NSBezierPath.bezierPathWithOvalInRect_(
        AppKit.NSMakeRect(center_x - 25 * s, center_y + 5 * s, 60 * s, 60 * s)
    ).fill()

    # Occhio con punto luce
    AppKit.NSColor.blackColor().set()
    AppKit.NSBezierPath.bezierPathWithOvalInRect_(
        AppKit.NSMakeRect(center_x + 8 * s, center_y + 35 * s, 13 * s, 13 * s)
    ).fill()
    AppKit.NSColor.whiteColor().set()
    AppKit.NSBezierPath.bezierPathWithOvalInRect_(
        AppKit.NSMakeRect(center_x + 13 * s, center_y + 40 * s, 5 * s, 5 * s)
    ).fill()

    # Becco d'Anatra Arancione Brillante
    AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.48, 0.0, 1.0).set()
    beak = AppKit.NSBezierPath.bezierPath()
    beak.moveToPoint_(AppKit.NSMakePoint(center_x + 18 * s, center_y + 36 * s))
    beak.lineToPoint_(AppKit.NSMakePoint(center_x + 55 * s, center_y + 26 * s))
    beak.lineToPoint_(AppKit.NSMakePoint(center_x + 18 * s, center_y + 16 * s))
    beak.closePath()
    beak.fill()

    # Occhialoni da Aviatore con riflesso azzurro
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.35, 0.25, 0.18, 1.0).set()
    AppKit.NSBezierPath.bezierPathWithRect_(
        AppKit.NSMakeRect(center_x - 25 * s, center_y + 28 * s, 60 * s, 10 * s)
    ).fill()

    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.75, 0.35, 1.0).set()
    goggle = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
        AppKit.NSMakeRect(center_x - 5 * s, center_y + 22 * s, 36 * s, 34 * s)
    )
    goggle.setLineWidth_(6.0 * s)
    goggle.stroke()
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.55, 0.88, 0.98, 0.75).set()
    goggle.fill()

    # Ala Inferiore Vintage
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.38, 0.32, 1.0).set()
    wing = AppKit.NSBezierPath.bezierPath()
    wing.moveToPoint_(AppKit.NSMakePoint(center_x - 50 * s, center_y - 8 * s))
    wing.lineToPoint_(AppKit.NSMakePoint(center_x + 50 * s, center_y - 8 * s))
    wing.lineToPoint_(AppKit.NSMakePoint(center_x + 20 * s, center_y - 75 * s))
    wing.lineToPoint_(AppKit.NSMakePoint(center_x - 30 * s, center_y - 75 * s))
    wing.closePath()
    wing.fill()

    # Ogiva & Elica Anteriore
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.25, 0.32, 1.0).set()
    AppKit.NSBezierPath.bezierPathWithOvalInRect_(
        AppKit.NSMakeRect(center_x + 95 * s, center_y - 12 * s, 26 * s, 26 * s)
    ).fill()

    # Elica con Motion Blur Rotante
    AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.94, 1.0, 0.75).set()
    prop = AppKit.NSBezierPath.bezierPath()
    prop.setLineWidth_(8.0 * s)
    prop.setLineCapStyle_(AppKit.NSLineCapStyleRound)
    prop.moveToPoint_(AppKit.NSMakePoint(center_x + 108 * s, center_y - 60 * s))
    prop.lineToPoint_(AppKit.NSMakePoint(center_x + 108 * s, center_y + 60 * s))
    prop.stroke()

    image.unlockFocus()

    # Save as PNG
    tiff_data = image.TIFFRepresentation()
    bitmap = AppKit.NSBitmapImageRep.imageRepsWithData_(tiff_data)[0]
    png_data = bitmap.representationUsingType_properties_(AppKit.NSBitmapImageFileTypePNG, None)
    png_data.writeToFile_atomically_(output_path, True)
    print(f"✅ Icon successfully generated: {output_path}")

if __name__ == "__main__":
    create_app_icon("assets/icon.png", 512)
