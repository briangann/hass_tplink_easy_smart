"""Prevent HA runtime imports from blocking unit tests.

custom_components/tplink_easy_smart/__init__.py imports HA at package load
time. Modules under test (coreapi.py, classes.py, etc.) don't need HA
themselves, so mock the whole homeassistant namespace before collection.
"""

import sys
from unittest.mock import MagicMock


def _mock_ha_modules() -> None:
    ha_modules = [
        "homeassistant",
        "homeassistant.config_entries",
        "homeassistant.const",
        "homeassistant.core",
        "homeassistant.components",
        "homeassistant.components.binary_sensor",
        "homeassistant.components.sensor",
        "homeassistant.components.switch",
        "homeassistant.exceptions",
        "homeassistant.helpers",
        "homeassistant.helpers.config_validation",
        "homeassistant.helpers.device_registry",
        "homeassistant.helpers.entity",
        "homeassistant.helpers.entity_platform",
        "homeassistant.helpers.service",
        "homeassistant.helpers.update_coordinator",
        "voluptuous",
    ]
    for mod in ha_modules:
        if mod not in sys.modules:
            sys.modules[mod] = MagicMock()


_mock_ha_modules()
