from __future__ import annotations
from typing import Dict, Type

from .base_renderer import BaseQtPilotRenderer
from .duck_renderer import QtDuckRenderer
from .captain_renderer import QtCaptainRenderer
from .chef_renderer import QtChefRenderer
from .owl_renderer import QtOwlRenderer
from .driver_renderer import QtDriverRenderer
from .zen_duck_renderer import QtZenDuckRenderer
from .gym_renderer import QtGymRenderer

RENDERER_MAP: Dict[str, Type[BaseQtPilotRenderer]] = {
    "duck": QtDuckRenderer,
    "captain": QtCaptainRenderer,
    "chef": QtChefRenderer,
    "owl": QtOwlRenderer,
    "driver": QtDriverRenderer,
    "zen_duck": QtZenDuckRenderer,
    "gym": QtGymRenderer,
}

def get_pilot_renderer(pilot_type: str) -> BaseQtPilotRenderer:
    """Factory function to get instantiated Qt pilot renderer."""
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
    "get_pilot_renderer",
    "RENDERER_MAP",
]
