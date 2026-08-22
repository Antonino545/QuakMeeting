"""
Backward-compatibility facade for ConfigManager.
Delegates to core.services.config_service.
"""
from core.services.config_service import (
    ConfigService,
    ConfigManager,
    config,
    CONFIG_DIR,
    CONFIG_PATH,
    DEFAULT_CONFIG
)

__all__ = [
    "ConfigService",
    "ConfigManager",
    "config",
    "CONFIG_DIR",
    "CONFIG_PATH",
    "DEFAULT_CONFIG"
]
