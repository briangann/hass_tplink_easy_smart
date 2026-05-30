"""Prevent HA runtime imports from blocking unit tests.

custom_components/tplink_easy_smart/__init__.py imports HA at package load
time. Modules under test (coreapi.py, classes.py, etc.) don't need HA
themselves, so mock the whole homeassistant namespace before collection.
"""

import sys
from dataclasses import dataclass
from unittest.mock import MagicMock


@dataclass(frozen=True)
class _StubEntityDescription:
    """Minimal real dataclass base so frozen dataclass subclasses resolve MRO and fields."""
    key: str = ""
    name: str | None = None
    icon: str | None = None
    device_class: object = None
    native_unit_of_measurement: str | None = None
    state_class: object = None


def _make_stub(name: str) -> type:
    """Create a uniquely-named stub base class supporting Generic[T] subscript."""
    def __init__(self, *args, **kwargs):  # noqa: ANN001
        pass
    def __class_getitem__(cls, item):  # noqa: ANN001
        return cls
    return type(name, (), {"__init__": __init__, "__class_getitem__": classmethod(__class_getitem__)})


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

    # Replace MagicMock stubs with real classes for HA base classes that are
    # inherited by @dataclass(frozen=True) subclasses — MRO traversal requires
    # a real type, not a MagicMock instance.
    sensor_mod = sys.modules["homeassistant.components.sensor"]
    sensor_mod.SensorEntityDescription = _StubEntityDescription  # type: ignore[attr-defined]
    sensor_mod.SensorEntity = _make_stub("SensorEntity")  # type: ignore[attr-defined]
    sensor_mod.SensorDeviceClass = MagicMock()  # type: ignore[attr-defined]
    sensor_mod.SensorStateClass = MagicMock()  # type: ignore[attr-defined]

    binary_mod = sys.modules["homeassistant.components.binary_sensor"]
    binary_mod.BinarySensorEntityDescription = _StubEntityDescription  # type: ignore[attr-defined]
    binary_mod.BinarySensorEntity = _make_stub("BinarySensorEntity")  # type: ignore[attr-defined]
    binary_mod.BinarySensorDeviceClass = MagicMock()  # type: ignore[attr-defined]

    switch_mod = sys.modules["homeassistant.components.switch"]
    switch_mod.SwitchEntityDescription = _StubEntityDescription  # type: ignore[attr-defined]
    switch_mod.SwitchEntity = _make_stub("SwitchEntity")  # type: ignore[attr-defined]

    coordinator_mod = sys.modules["homeassistant.helpers.update_coordinator"]
    class _CoordinatorEntityStub:
        def __init__(self, coordinator, *args, **kwargs):  # type: ignore[misc]
            self.coordinator = coordinator
        def _handle_coordinator_update(self) -> None:  # type: ignore[misc]
            pass
        def __class_getitem__(cls, item):  # type: ignore[misc]
            return cls

    core_mod = sys.modules["homeassistant.core"]
    core_mod.callback = lambda fn: fn  # type: ignore[attr-defined]

    coordinator_mod.CoordinatorEntity = _CoordinatorEntityStub  # type: ignore[attr-defined]
    coordinator_mod.DataUpdateCoordinator = _make_stub("DataUpdateCoordinator")  # type: ignore[attr-defined]


_mock_ha_modules()
