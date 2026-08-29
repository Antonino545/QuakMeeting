from __future__ import annotations
from ui.linux.theme import Theme
from typing import Dict, Type

from .base_renderer import BaseQtPilotRenderer
from .duck_renderer import QtDuckRenderer
from .captain_renderer import QtCaptainRenderer
from .chef_renderer import QtChefRenderer
from .owl_renderer import QtOwlRenderer
from .driver_renderer import QtDriverRenderer
from .zen_duck_renderer import QtZenDuckRenderer
from .gym_renderer import QtGymRenderer
from .platypus_renderer import QtPlatypusRenderer
from .squirrel_renderer import QtSquirrelRenderer

from .modular_renderer import QtModularRenderer

RENDERER_MAP: Dict[str, Type[BaseQtPilotRenderer]] = {
    "duck": QtDuckRenderer,
    "captain": QtCaptainRenderer,
    "chef": QtChefRenderer,
    "owl": QtOwlRenderer,
    "driver": QtDriverRenderer,
    "zen_duck": QtZenDuckRenderer,
    "gym": QtGymRenderer,
    "platypus": QtPlatypusRenderer,
    "squirrel": QtSquirrelRenderer,
}

def get_pilot_renderer(pilot_type: str, animal: str = None, outfit: str = None) -> BaseQtPilotRenderer:
    """Factory function to get instantiated Qt pilot renderer."""
    if animal and outfit:
        return QtModularRenderer(animal=animal, outfit=outfit)

    if "_" in pilot_type and pilot_type not in ("zen_duck",):
        parts = pilot_type.split("_", 1)
        if parts[0] in ("duck", "owl", "bunny"):
            return QtModularRenderer(animal=parts[0], outfit=parts[1])

    if pilot_type == "bunny":
        return QtModularRenderer(animal="bunny", outfit="aviator")

    cls = RENDERER_MAP.get(pilot_type, QtDuckRenderer)
    return cls()

__all__ = [
    "BaseQtPilotRenderer",
    "QtDuckRenderer",
    "QtCaptainRenderer",
    "QtChefRenderer",
    "QtOwlRenderer",
    "QtDriverRenderer",
    "QtZenDuckRenderer",
    "QtGymRenderer",
    "QtPlatypusRenderer",
    "QtSquirrelRenderer",
    "QtModularRenderer",
    "get_pilot_renderer",
    "RENDERER_MAP",
]
