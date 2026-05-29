"""Support for switches."""

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .client.const import FEATURE_POE

from .const import (
    DEFAULT_POE_STATE_SWITCHES,
    DEFAULT_PORT_STATE_SWITCHES,
    OPT_POE_STATE_SWITCHES,
    OPT_PORT_STATE_SWITCHES,
)
from .helpers import (
    generate_entity_id,
    generate_entity_name,
    generate_entity_unique_id,
    get_coordinator,
)
from .update_coordinator import TpLinkDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


_FUNCTION_DISPLAYED_NAME_PORT_STATE_FORMAT: Final = "Port {} enabled"
_FUNCTION_UID_PORT_STATE_FORMAT: Final = "port_{}_enabled"

_FUNCTION_DISPLAYED_NAME_PORT_POE_STATE_FORMAT: Final = "Port {} PoE enabled"
_FUNCTION_UID_PORT_POE_STATE_FORMAT: Final = "port_{}_poe_enabled"

ENTITY_DOMAIN: Final = "switch"


# ---------------------------
#   TpLinkSwitchEntityDescription
# ---------------------------
@dataclass(frozen=True)
class TpLinkSwitchEntityDescription(SwitchEntityDescription):
    """A class that describes switch."""

    function_name: str | None = None
    function_uid: str | None = None
    device_name: str | None = None


# ---------------------------
#   TpLinkPortSwitchEntityDescription
# ---------------------------
@dataclass(frozen=True)
class TpLinkPortSwitchEntityDescription(TpLinkSwitchEntityDescription):
    """A class that describes port switch."""

    port_number: int | None = None


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for TP-Link component."""
    coordinator: TpLinkDataUpdateCoordinator = get_coordinator(hass, config_entry)
    switch_info = coordinator.get_switch_info()
    device_name = switch_info.name if switch_info else None

    sensors = []

    if config_entry.options.get(OPT_PORT_STATE_SWITCHES, DEFAULT_PORT_STATE_SWITCHES):
        for port_number in range(1, coordinator.ports_count + 1):
            function_name = _FUNCTION_DISPLAYED_NAME_PORT_STATE_FORMAT.format(port_number)
            sensors.append(
                TpLinkPortStateSwitch(
                    coordinator,
                    TpLinkPortSwitchEntityDescription(
                        key=f"port_{port_number}_enabled",
                        icon="mdi:ethernet",
                        name=generate_entity_name(function_name, device_name) if device_name else None,
                        port_number=port_number,
                        device_name=device_name,
                        function_uid=_FUNCTION_UID_PORT_STATE_FORMAT.format(port_number),
                        function_name=function_name,
                    ),
                )
            )

    if config_entry.options.get(
        OPT_POE_STATE_SWITCHES, DEFAULT_POE_STATE_SWITCHES
    ) and await coordinator.is_feature_available(FEATURE_POE):
        for port_number in range(1, coordinator.ports_poe_count + 1):
            function_name = _FUNCTION_DISPLAYED_NAME_PORT_POE_STATE_FORMAT.format(port_number)
            sensors.append(
                TpLinkPortPoeStateSwitch(
                    coordinator,
                    TpLinkPortSwitchEntityDescription(
                        key=f"port_{port_number}_poe_enabled",
                        icon="mdi:lightning-bolt-outline",
                        name=generate_entity_name(function_name, device_name) if device_name else None,
                        port_number=port_number,
                        device_name=device_name,
                        function_uid=_FUNCTION_UID_PORT_POE_STATE_FORMAT.format(port_number),
                        function_name=function_name,
                    ),
                )
            )

    async_add_entities(sensors)


# ---------------------------
#   TpLinkSwitch
# ---------------------------
class TpLinkSwitch(  # pyright: ignore[reportIncompatibleVariableOverride]
    CoordinatorEntity[TpLinkDataUpdateCoordinator], SwitchEntity, ABC
):
    entity_description: TpLinkSwitchEntityDescription  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkSwitchEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self.entity_description = description  # pyright: ignore[reportIncompatibleVariableOverride]
        self._attr_device_info = coordinator.get_device_info()
        self._attr_unique_id = generate_entity_unique_id(
            coordinator, description.function_uid
        )
        self._is_available = True
        self.entity_id = generate_entity_id(
            coordinator, ENTITY_DOMAIN, description.function_name
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()
        _LOGGER.debug("Switch %s added to hass", self.entity_description.name)

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return if entity is available."""
        return self.is_on is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()

    @abstractmethod
    async def _go_to_state(self, state: bool):
        raise NotImplementedError()

    async def __go_to_state(self, state: bool):
        """Perform transition to the specified state."""
        await self._go_to_state(state)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """async_turn_off."""
        await self.__go_to_state(False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """async_turn_on."""
        await self.__go_to_state(True)

    def turn_on(self, **kwargs: Any) -> None:
        """turn_on."""
        return asyncio.run_coroutine_threadsafe(
            self.async_turn_on(**kwargs), self.hass.loop
        ).result()

    def turn_off(self, **kwargs: Any) -> None:
        """turn_off."""
        return asyncio.run_coroutine_threadsafe(
            self.async_turn_off(**kwargs), self.hass.loop
        ).result()


# ---------------------------
#   TpLinkPortStateSwitch
# ---------------------------
class TpLinkPortStateSwitch(TpLinkSwitch):
    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkPortSwitchEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description)
        self._attr_is_on = None
        self._attr_extra_state_attributes = {}
        self._port_number = description.port_number

    async def _go_to_state(self, state: bool):
        info = self._port_info
        if not info:
            _LOGGER.warning(
                "Can not change switch '%s' state: port info not found", self.name
            )
            return
        await self.coordinator.set_port_state(
            info.number, state, info.speed_config, info.flow_control_config
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._port_number is None:
            return
        self._port_info = self.coordinator.get_port_state(self._port_number)
        self._attr_is_on = self._port_info.enabled if self._port_info else None
        super()._handle_coordinator_update()


# ---------------------------
#   TpLinkPortPoeStateSwitch
# ---------------------------
class TpLinkPortPoeStateSwitch(TpLinkSwitch):
    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkPortSwitchEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description)
        self._attr_is_on = None
        self._attr_extra_state_attributes = {}
        self._port_number = description.port_number

    async def _go_to_state(self, state: bool):
        info = self._port_poe_info
        if not info:
            _LOGGER.warning(
                "Can not change switch '%s' PoE state: port info not found", self.name
            )
            return
        await self.coordinator.async_set_port_poe_settings(
            info.number, state, info.priority, info.power_limit
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._port_number is None:
            return
        self._port_poe_info = self.coordinator.get_port_poe_state(self._port_number)
        self._attr_is_on = self._port_poe_info.enabled if self._port_poe_info else None
        super()._handle_coordinator_update()
