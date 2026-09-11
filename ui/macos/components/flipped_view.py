import AppKit


class FlippedView(AppKit.NSView):
    """Container view with Cocoa top-left coordinate origin for natural vertical layout."""

    def isFlipped(self):
        return True
