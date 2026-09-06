"""
Qt-style Relative Layout Components (VBox, HBox) for macOS AppKit using NSStackView.
Provides high-level, declarative layout capabilities similar to QVBoxLayout and QHBoxLayout.
"""

import AppKit
import objc


class BaseStack(AppKit.NSStackView):
    """Base class providing Qt-like convenience methods over NSStackView."""

    @objc.python_method
    def add_widget(self, view: AppKit.NSView, spacing: float = None):
        """Adds a child view to the arranged layout stack."""
        self.addArrangedSubview_(view)
        if spacing is not None:
            self.setCustomSpacing_afterView_(float(spacing), view)

    @objc.python_method
    def add_widgets(self, *views):
        """Adds multiple child views in sequential order."""
        for v in views:
            self.addArrangedSubview_(v)

    @objc.python_method
    def add_stretch(self):
        """Appends a flexible spacer view that expands to fill remaining space, matching Qt addStretch()."""
        spacer = AppKit.NSView.alloc().initWithFrame_(AppKit.NSZeroRect)
        spacer.setTranslatesAutoresizingMaskIntoConstraints_(False)
        orient = self.orientation()
        if orient == AppKit.NSUserInterfaceLayoutOrientationHorizontal:
            spacer.setContentHuggingPriority_forOrientation_(
                AppKit.NSLayoutPriorityFittingSizeCompression,
                AppKit.NSLayoutConstraintOrientationHorizontal,
            )
        else:
            spacer.setContentHuggingPriority_forOrientation_(
                AppKit.NSLayoutPriorityFittingSizeCompression,
                AppKit.NSLayoutConstraintOrientationVertical,
            )
        self.addArrangedSubview_(spacer)
        return spacer

    @objc.python_method
    def set_spacing(self, spacing: float):
        """Sets the uniform inter-item spacing in points."""
        self.setSpacing_(float(spacing))

    @objc.python_method
    def set_padding(self, top: float = 0.0, right: float = 0.0, bottom: float = 0.0, left: float = 0.0):
        """Sets inner padding edge insets."""
        self.setEdgeInsets_(AppKit.NSEdgeInsetsMake(top, left, bottom, right))


class VBox(BaseStack):
    """
    Vertical layout stack, equivalent to Qt's QVBoxLayout.
    Arranges child views sequentially from top to bottom.
    """

    def init(self):
        self = objc.super(VBox, self).initWithFrame_(AppKit.NSZeroRect)
        if self is None:
            return None
        self.setOrientation_(AppKit.NSUserInterfaceLayoutOrientationVertical)
        self.setAlignment_(AppKit.NSLayoutAttributeLeading)
        self.setDistribution_(AppKit.NSStackViewDistributionFill)
        self.setSpacing_(8.0)
        return self

    @classmethod
    @objc.python_method
    def create(cls, spacing: float = 8.0, alignment=AppKit.NSLayoutAttributeLeading, parent=None):
        """Factory method to instantiate a configured vertical layout box."""
        box = cls.alloc().init()
        box.setSpacing_(float(spacing))
        box.setAlignment_(alignment)
        if parent is not None:
            parent.addSubview_(box)
        return box


class HBox(BaseStack):
    """
    Horizontal layout stack, equivalent to Qt's QHBoxLayout.
    Arranges child views sequentially from left to right.
    """

    def init(self):
        self = objc.super(HBox, self).initWithFrame_(AppKit.NSZeroRect)
        if self is None:
            return None
        self.setOrientation_(AppKit.NSUserInterfaceLayoutOrientationHorizontal)
        self.setAlignment_(AppKit.NSLayoutAttributeCenterY)
        self.setDistribution_(AppKit.NSStackViewDistributionFill)
        self.setSpacing_(8.0)
        return self

    @classmethod
    @objc.python_method
    def create(cls, spacing: float = 8.0, alignment=AppKit.NSLayoutAttributeCenterY, parent=None):
        """Factory method to instantiate a configured horizontal layout box."""
        box = cls.alloc().init()
        box.setSpacing_(float(spacing))
        box.setAlignment_(alignment)
        if parent is not None:
            parent.addSubview_(box)
        return box


__all__ = ["BaseStack", "VBox", "HBox"]
