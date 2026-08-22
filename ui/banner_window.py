"""
Backward-compatibility facade for QuakMeeting banner window.
Delegates to modular components in ui.banner.
"""
from ui.banner import (
    QuakPitFlyingBanner,
    _run_banner,
    show_banner_async,
    QuakPitBannerView,
    get_pilot_renderer
)

__all__ = [
    "QuakPitFlyingBanner",
    "_run_banner",
    "show_banner_async",
    "QuakPitBannerView",
    "get_pilot_renderer"
]
