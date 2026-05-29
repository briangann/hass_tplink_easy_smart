"""Tests for helpers.py."""

import pytest
from unittest.mock import MagicMock, patch

from custom_components.tplink_easy_smart.client.classes import TpLinkSystemInfo
from custom_components.tplink_easy_smart.helpers import (
    ConfigurationError,
    generate_entity_id,
    generate_entity_name,
    generate_entity_unique_id,
    get_coordinator,
)
from custom_components.tplink_easy_smart.const import DATA_KEY_COORDINATOR, DOMAIN


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def coordinator():
    mock = MagicMock()
    mock.name = "tplink_easy_smart"
    mock.unique_id = "abc123"
    mock.get_switch_info.return_value = TpLinkSystemInfo(
        name="SG108PE", mac="AA:BB:CC:DD:EE:FF"
    )
    return mock


# ---------------------------------------------------------------------------
# generate_entity_name
# ---------------------------------------------------------------------------

class TestGenerateEntityName:
    def test_combines_device_and_function(self):
        assert generate_entity_name("Network info", "SG108PE") == "SG108PE Network info"

    def test_order_device_first(self):
        result = generate_entity_name("Port 1 state", "MySwitch")
        assert result.startswith("MySwitch")
        assert "Port 1 state" in result

    def test_single_word_names(self):
        assert generate_entity_name("Speed", "Switch") == "Switch Speed"


# ---------------------------------------------------------------------------
# generate_entity_unique_id
# ---------------------------------------------------------------------------

class TestGenerateEntityUniqueId:
    def test_includes_prefix_uid_and_mac(self, coordinator):
        result = generate_entity_unique_id(coordinator, "network_info")
        assert "abc123" in result
        assert "network_info" in result
        assert "aa:bb:cc:dd:ee:ff" in result  # lowercased

    def test_mac_lowercased(self, coordinator):
        result = generate_entity_unique_id(coordinator, "port_1_state")
        assert "AA" not in result  # uppercase MAC not present

    def test_none_uid_uses_empty_string(self, coordinator):
        result = generate_entity_unique_id(coordinator, None)
        # format is {prefix}__{suffix} when uid is None
        assert "abc123" in result
        assert result.count("_") >= 2

    def test_none_switch_info_uses_empty_suffix(self, coordinator):
        coordinator.get_switch_info.return_value = None
        result = generate_entity_unique_id(coordinator, "port_1")
        assert result == "abc123_port_1_"

    def test_none_mac_uses_empty_suffix(self, coordinator):
        coordinator.get_switch_info.return_value = TpLinkSystemInfo(name="Switch", mac=None)
        result = generate_entity_unique_id(coordinator, "port_1")
        assert result == "abc123_port_1_"

    def test_format_is_prefix_uid_suffix(self, coordinator):
        result = generate_entity_unique_id(coordinator, "uid")
        assert result == "abc123_uid_aa:bb:cc:dd:ee:ff"


# ---------------------------------------------------------------------------
# generate_entity_id
# ---------------------------------------------------------------------------

class TestGenerateEntityId:
    def test_calls_hass_generate_id_with_correct_preferred_id(self, coordinator):
        with patch(
            "custom_components.tplink_easy_smart.helpers.hass_generate_id",
            side_effect=lambda fmt, preferred, hass: preferred,
        ) as mock_gen:
            result = generate_entity_id(coordinator, "sensor", "Network info")
            mock_gen.assert_called_once()
            _, preferred = mock_gen.call_args[0]
            assert "tplink_easy_smart" in preferred
            assert "Network info" in preferred

    def test_none_function_name_uses_empty_string(self, coordinator):
        with patch(
            "custom_components.tplink_easy_smart.helpers.hass_generate_id",
            side_effect=lambda fmt, preferred, hass: preferred,
        ) as mock_gen:
            generate_entity_id(coordinator, "sensor", None)
            _, preferred = mock_gen.call_args[0]
            assert "tplink_easy_smart" in preferred
            # trailing space from empty function name is acceptable
            assert preferred == "tplink_easy_smart "

    def test_domain_format_string_passed(self, coordinator):
        with patch(
            "custom_components.tplink_easy_smart.helpers.hass_generate_id",
            side_effect=lambda fmt, preferred, hass: fmt,
        ) as mock_gen:
            result = generate_entity_id(coordinator, "binary_sensor", "Port 1")
            assert result == "binary_sensor.{}"


# ---------------------------------------------------------------------------
# ConfigurationError
# ---------------------------------------------------------------------------

class TestConfigurationError:
    def test_str_returns_message(self):
        err = ConfigurationError("coordinator not found")
        assert str(err) == "coordinator not found"

    def test_is_exception(self):
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("test")


# ---------------------------------------------------------------------------
# get_coordinator
# ---------------------------------------------------------------------------

class TestGetCoordinator:
    def test_returns_coordinator_when_present(self):
        fake_coordinator = MagicMock()
        hass = MagicMock()
        hass.data = {
            DOMAIN: {
                "entry_abc": {DATA_KEY_COORDINATOR: fake_coordinator}
            }
        }
        config_entry = MagicMock()
        config_entry.entry_id = "entry_abc"

        result = get_coordinator(hass, config_entry)
        assert result is fake_coordinator

    def test_raises_when_coordinator_missing(self):
        hass = MagicMock()
        hass.data = {}
        config_entry = MagicMock()
        config_entry.entry_id = "missing"

        with pytest.raises(ConfigurationError):
            get_coordinator(hass, config_entry)

    def test_raises_when_domain_missing(self):
        hass = MagicMock()
        hass.data = {"other_domain": {}}
        config_entry = MagicMock()
        config_entry.entry_id = "entry_abc"

        with pytest.raises(ConfigurationError):
            get_coordinator(hass, config_entry)
