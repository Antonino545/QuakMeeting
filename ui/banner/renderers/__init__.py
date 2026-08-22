from typing import Dict, Type
from .base_renderer import BasePilotRenderer
from .duck_renderer import DuckPilotRenderer
from .captain_renderer import CaptainPilotRenderer
from .chef_renderer import ChefPilotRenderer
from .owl_renderer import OwlPilotRenderer
from .driver_renderer import DriverPilotRenderer
from .zen_duck_renderer import ZenDuckRenderer

RENDERER_MAP: Dict[str, Type[BasePilotRenderer]] = {
    "duck": DuckPilotRenderer,
    "captain": CaptainPilotRenderer,
    "chef": ChefPilotRenderer,
    "owl": OwlPilotRenderer,
    "driver": DriverPilotRenderer,
    "zen_duck": ZenDuckRenderer
}

def get_pilot_renderer(pilot_type: str) -> BasePilotRenderer:
    """Factory function to get instantiated pilot renderer."""
    cls = RENDERER_MAP.get(pilot_type, DuckPilotRenderer)
    return cls()

__all__ = [
    "BasePilotRenderer",
    "DuckPilotRenderer",
    "CaptainPilotRenderer",
    "ChefPilotRenderer",
    "OwlPilotRenderer",
    "DriverPilotRenderer",
    "ZenDuckRenderer",
    "get_pilot_renderer",
    "RENDERER_MAP"
]
