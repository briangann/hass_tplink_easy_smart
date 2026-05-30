"""Tests for sensor.py."""

from unittest.mock import MagicMock, patch

from custom_components.tplink_easy_smart.client.classes import TpLinkSystemInfo


def make_coordinator(system_info=None, poe_state=None):
    coordinator = MagicMock()
    coordinator.get_switch_info.return_value = system_info
    coordinator.get_poe_state.return_value = poe_state
    coordinator.get_device_info.return_value = {}
    coordinator.name = "tplink_easy_smart"
    coordinator.unique_id = "abc123"
    return coordinator


class TestTpLinkNetworkInfoSensor:
    def _make_sensor(self, system_info):
        from custom_components.tplink_easy_smart.sensor import (
            TpLinkNetworkInfoSensor,
            TpLinkSensorEntityDescription,
        )
        coordinator = make_coordinator(system_info=system_info)
        description = TpLinkSensorEntityDescription(
            key="network_info",
            function_uid="network_info",
            function_name="Network info",
        )
        with patch(
            "custom_components.tplink_easy_smart.sensor.generate_entity_id",
            return_value="sensor.test",
        ), patch(
            "custom_components.tplink_easy_smart.sensor.generate_entity_unique_id",
            return_value="uid_network_info",
        ):
            sensor = TpLinkNetworkInfoSensor(coordinator, description)
        sensor._handle_coordinator_update()
        return sensor

    def test_exposes_ip_as_native_value(self):
        info = TpLinkSystemInfo(ip="192.168.1.10")
        sensor = self._make_sensor(info)
        assert sensor._attr_native_value == "192.168.1.10"

    def test_exposes_mac(self):
        info = TpLinkSystemInfo(mac="6C:4C:BC:42:31:AE")
        sensor = self._make_sensor(info)
        assert sensor._attr_extra_state_attributes["mac"] == "6C:4C:BC:42:31:AE"

    def test_exposes_firmware(self):
        info = TpLinkSystemInfo(firmware="1.0.0 Build 20230616 Rel.57668")
        sensor = self._make_sensor(info)
        assert sensor._attr_extra_state_attributes["firmware"] == "1.0.0 Build 20230616 Rel.57668"

    def test_exposes_hardware(self):
        info = TpLinkSystemInfo(hardware="TL-SG1218MPE 1.0")
        sensor = self._make_sensor(info)
        assert sensor._attr_extra_state_attributes["hardware"] == "TL-SG1218MPE 1.0"

    def test_firmware_none_when_not_set(self):
        info = TpLinkSystemInfo()
        sensor = self._make_sensor(info)
        assert sensor._attr_extra_state_attributes["firmware"] is None

    def test_unavailable_when_no_system_info(self):
        sensor = self._make_sensor(None)
        assert sensor._attr_available is False
