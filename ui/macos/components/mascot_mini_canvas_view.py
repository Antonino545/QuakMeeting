import AppKit
import objc
from ui.macos.theme import Theme
from ui.macos.banner.renderers.modular_renderer import ModularPilotRenderer


class MascotMiniCanvasView(AppKit.NSView):
    """Mini embedded live vector mascot canvas for category cards and previews."""

    def initWithFrame_animal_outfit_(self, frame, animal, outfit):
        self = objc.super(MascotMiniCanvasView, self).initWithFrame_(frame)
        self.animal = animal
        self.outfit = outfit
        self.tick = 0
        self.setWantsLayer_(True)
        self.layer().setCornerRadius_(10.0)
        self.layer().setMasksToBounds_(True)
        self.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
        self.layer().setBorderWidth_(1.0)
        self.layer().setBorderColor_(Theme.SURFACE1.CGColor())
        self.bg_color = Theme.MANTLE
        return self

    def setAccentColor_(self, color):
        self.layer().setBorderColor_(color.colorWithAlphaComponent_(0.35).CGColor())
        self.setNeedsDisplay_(True)

    def setCustomCornerRadius_(self, radius):
        self.layer().setCornerRadius_(radius)
        self.setNeedsDisplay_(True)

    def setBgColor_(self, color):
        self.bg_color = color
        self.layer().setBackgroundColor_(color.CGColor())
        self.setNeedsDisplay_(True)

    def updateAnimal_(self, animal):
        self.animal = animal
        self.setNeedsDisplay_(True)

    def updateOutfit_(self, outfit):
        self.outfit = outfit
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        bounds = self.bounds()
        w = bounds.size.width
        h = bounds.size.height

        # Background
        bg = getattr(self, "bg_color", Theme.MANTLE)
        bg.set()
        AppKit.NSRectFill(bounds)

        # Scale down slightly to fit mini card viewport (macOS standard Quartz coordinates)
        ctx = AppKit.NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()

        scale = 0.62 if h <= 62.0 else 0.68
        transform = AppKit.NSAffineTransform.transform()
        transform.translateXBy_yBy_(w * 0.5, h * 0.5 - 2.0)
        transform.scaleBy_(scale)
        transform.concat()

        renderer = ModularPilotRenderer(animal=self.animal, outfit=self.outfit)
        renderer.draw_pilot(0, 0, self.tick)

        ctx.restoreGraphicsState()
