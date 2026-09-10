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
        return self

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

        # Soft background
        Theme.MANTLE.set()
        AppKit.NSRectFill(bounds)

        # Scale down slightly to fit mini card viewport (macOS standard Quartz coordinates)
        ctx = AppKit.NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()

        transform = AppKit.NSAffineTransform.transform()
        transform.translateXBy_yBy_(w * 0.5 - 2, h * 0.5 - 2)
        transform.scaleBy_(0.68)
        transform.concat()

        renderer = ModularPilotRenderer(animal=self.animal, outfit=self.outfit)
        renderer.draw_pilot(0, 0, self.tick)

        ctx.restoreGraphicsState()
