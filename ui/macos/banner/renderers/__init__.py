from typing import Dict, Type
from .base_renderer import BasePilotRenderer
from .duck_renderer import DuckPilotRenderer
from .captain_renderer import CaptainPilotRenderer
from .chef_renderer import ChefPilotRenderer
from .owl_renderer import OwlPilotRenderer
from .driver_renderer import DriverPilotRenderer
from .zen_duck_renderer import ZenDuckRenderer
from .gym_renderer import GymPilotRenderer
from .platypus_renderer import PlatypusPilotRenderer
from .squirrel_renderer import SquirrelPilotRenderer

from .modular_renderer import ModularPilotRenderer

RENDERER_MAP: Dict[str, Type[BasePilotRenderer]] = {
    "duck": DuckPilotRenderer,
    "captain": CaptainPilotRenderer,
    "chef": ChefPilotRenderer,
    "owl": OwlPilotRenderer,
    "driver": DriverPilotRenderer,
    "zen_duck": ZenDuckRenderer,
    "gym": GymPilotRenderer,
    "platypus": PlatypusPilotRenderer,
    "squirrel": SquirrelPilotRenderer,
}

def get_pilot_renderer(pilot_type: str, animal: str = None, outfit: str = None) -> BasePilotRenderer:
    """Factory function to get instantiated pilot renderer."""
    if animal and outfit:
        return ModularPilotRenderer(animal=animal, outfit=outfit)

    if "_" in pilot_type and pilot_type not in ("zen_duck",):
        parts = pilot_type.split("_", 1)
        if parts[0] in ("duck", "owl", "bunny", "platypus", "squirrel"):
            return ModularPilotRenderer(animal=parts[0], outfit=parts[1])

    if pilot_type == "bunny":
        return ModularPilotRenderer(animal="bunny", outfit="aviator")

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
    "GymPilotRenderer",
    "PlatypusPilotRenderer",
    "SquirrelPilotRenderer",
    "ModularPilotRenderer",
    "get_pilot_renderer",
    "RENDERER_MAP"
]

