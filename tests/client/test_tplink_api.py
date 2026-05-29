"""Tests for tplink_api.py parsing logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.tplink_easy_smart.client.classes import (
    PoeClass,
    PoePowerLimit,
    PoePowerStatus,
    PoePriority,
    PortSpeed,
)
from custom_components.tplink_easy_smart.client.tplink_api import TpLinkApi


# ---------------------------------------------------------------------------
# Fixture — TpLinkApi with mocked core_api and feature detector
# ---------------------------------------------------------------------------

@pytest.fixture
def api():
    """TpLinkApi with mocked internals — no real HTTP calls."""
    instance = TpLinkApi.__new__(TpLinkApi)
    instance._core_api = MagicMock()
    instance._core_api.get_variables = AsyncMock(return_value=None)
    instance._core_api.get_variable = AsyncMock(return_value=None)
    instance._is_features_updated = True
    instance._features = MagicMock()
    instance._features.is_available = MagicMock(return_value=True)
    return instance


# ---------------------------------------------------------------------------
# Fixture data — realistic device responses
# ---------------------------------------------------------------------------

PORT_STATE_DATA = {
    "all_info": {
        "state":   [1, 0, 1],
        "spd_cfg": [1, 1, 1],
        "spd_act": [6, 0, 5],
        "fc_cfg":  [0, 0, 1],
        "fc_act":  [0, 0, 0],
    },
    "max_port_num": 3,
}

STATS_DATA = {
    "all_info": {
        "pkts":  [100, 5, 200, 3,   # port 1
                  50,  0,  75, 1],  # port 2
        "state": [1, 1],
    },
    "max_port_num": 2,
}

POE_PORT_DATA = {
    "portConfig": {
        "state":       [1, 0],
        "priority":    [0, 2],           # HIGH, LOW
        "powerlimit":  [330, 40],        # AUTO, CLASS_1
        "power":       [150, 0],         # /10 → 15.0W, 0W
        "current":     [500, 0],         # raw mA
        "voltage":     [480, 0],         # /10 → 48.0V, 0V
        "pdclass":     [40, 330],        # CLASS_1, CLASS_0
        "powerstatus": [2, 0],           # ON, OFF
    },
    "poe_port_num": 2,
}

DEVICE_INFO_DATA = {
    "descriStr":  ["TL-SG108PE"],
    "macStr":     ["AA:BB:CC:DD:EE:FF"],
    "ipStr":      ["192.168.1.10"],
    "netmaskStr": ["255.255.255.0"],
    "gatewayStr": ["192.168.1.1"],
    "firmwareStr": ["1.0.6 Build 20221208"],
    "hardwareStr": ["TL-SG108PE 5.0"],
}

POE_GLOBAL_CONFIG = {
    "system_power_limit":       1500,  # /10 → 150.0
    "system_power_remain":      1200,  # /10 → 120.0
    "system_power_limit_min":     10,  # /10 → 1.0
    "system_power_limit_max":   1500,  # /10 → 150.0
    "system_power_consumption":  300,  # /10 → 30.0
}


# ---------------------------------------------------------------------------
# get_port_states
# ---------------------------------------------------------------------------

class TestGetPortStates:
    @pytest.mark.asyncio
    async def test_returns_empty_when_data_none(self, api):
        api._core_api.get_variables.return_value = None
        result = await api.get_port_states()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_info_missing(self, api):
        api._core_api.get_variables.return_value = {"max_port_num": 3}
        result = await api.get_port_states()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_max_port_num_missing(self, api):
        api._core_api.get_variables.return_value = {"all_info": {"state": [1]}}
        result = await api.get_port_states()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_keys_missing_from_all_info(self, api):
        api._core_api.get_variables.return_value = {
            "all_info": {"state": [1]},  # missing spd_cfg etc.
            "max_port_num": 1,
        }
        result = await api.get_port_states()
        assert result == []

    @pytest.mark.asyncio
    async def test_parses_port_count(self, api):
        api._core_api.get_variables.return_value = PORT_STATE_DATA
        result = await api.get_port_states()
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_port_numbers_sequential(self, api):
        api._core_api.get_variables.return_value = PORT_STATE_DATA
        result = await api.get_port_states()
        assert [p.number for p in result] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_enabled_flag_parsed(self, api):
        api._core_api.get_variables.return_value = PORT_STATE_DATA
        result = await api.get_port_states()
        assert result[0].enabled is True   # state[0] == 1
        assert result[1].enabled is False  # state[1] == 0
        assert result[2].enabled is True   # state[2] == 1

    @pytest.mark.asyncio
    async def test_speed_actual_parsed(self, api):
        api._core_api.get_variables.return_value = PORT_STATE_DATA
        result = await api.get_port_states()
        assert result[0].speed_actual == PortSpeed.FULL_1000M  # spd_act[0] == 6
        assert result[1].speed_actual == PortSpeed.LINK_DOWN   # spd_act[1] == 0
        assert result[2].speed_actual == PortSpeed.FULL_100M   # spd_act[2] == 5

    @pytest.mark.asyncio
    async def test_flow_control_parsed(self, api):
        api._core_api.get_variables.return_value = PORT_STATE_DATA
        result = await api.get_port_states()
        assert result[2].flow_control_config is True   # fc_cfg[2] == 1

    @pytest.mark.asyncio
    async def test_bounds_guard_short_arrays(self, api):
        # max_port_num says 5 but arrays only have 2 entries
        api._core_api.get_variables.return_value = {
            "all_info": {
                "state":   [1, 0],
                "spd_cfg": [1, 1],
                "spd_act": [6, 0],
                "fc_cfg":  [0, 0],
                "fc_act":  [0, 0],
            },
            "max_port_num": 5,
        }
        result = await api.get_port_states()
        assert len(result) == 2  # stops at array boundary, not max_port_num


# ---------------------------------------------------------------------------
# get_port_statistics
# ---------------------------------------------------------------------------

class TestGetPortStatistics:
    @pytest.mark.asyncio
    async def test_returns_empty_when_feature_unavailable(self, api):
        api._features.is_available.return_value = False
        result = await api.get_port_statistics()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_data_none(self, api):
        api._core_api.get_variables.return_value = None
        result = await api.get_port_statistics()
        assert result == []

    @pytest.mark.asyncio
    async def test_parses_port_count(self, api):
        api._core_api.get_variables.return_value = STATS_DATA
        result = await api.get_port_statistics()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_packet_counts_parsed(self, api):
        api._core_api.get_variables.return_value = STATS_DATA
        result = await api.get_port_statistics()
        assert result[0].tx_good_pkts == 100
        assert result[0].tx_bad_pkts == 5
        assert result[0].rx_good_pkts == 200
        assert result[0].rx_bad_pkts == 3
        assert result[1].tx_good_pkts == 50
        assert result[1].rx_bad_pkts == 1

    @pytest.mark.asyncio
    async def test_enabled_flag_parsed(self, api):
        api._core_api.get_variables.return_value = STATS_DATA
        result = await api.get_port_statistics()
        assert result[0].enabled is True
        assert result[1].enabled is True

    @pytest.mark.asyncio
    async def test_bounds_guard_short_pkts(self, api):
        # pkts array only covers 1 port but max_port_num says 3
        api._core_api.get_variables.return_value = {
            "all_info": {
                "pkts":  [10, 0, 20, 0],  # 1 port
                "state": [1, 1, 1],
            },
            "max_port_num": 3,
        }
        result = await api.get_port_statistics()
        assert len(result) == 1


# ---------------------------------------------------------------------------
# get_poe_state
# ---------------------------------------------------------------------------

class TestGetPoeState:
    @pytest.mark.asyncio
    async def test_returns_none_when_feature_unavailable(self, api):
        api._features.is_available.return_value = False
        result = await api.get_poe_state()
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_config_not_dict(self, api):
        api._core_api.get_variable.return_value = None
        result = await api.get_poe_state()
        assert result is None

    @pytest.mark.asyncio
    async def test_parses_power_values_with_scaling(self, api):
        api._core_api.get_variable.return_value = POE_GLOBAL_CONFIG
        result = await api.get_poe_state()
        assert result is not None
        assert result.power_limit == 150.0
        assert result.power_remain == 120.0
        assert result.power_limit_min == 1.0
        assert result.power_limit_max == 150.0
        assert result.power_consumption == 30.0


# ---------------------------------------------------------------------------
# get_device_info
# ---------------------------------------------------------------------------

class TestGetDeviceInfo:
    @pytest.mark.asyncio
    async def test_returns_systeminfo_when_data_none(self, api):
        api._core_api.get_variable.return_value = None
        result = await api.get_device_info()
        assert result.name is None
        assert result.mac is None

    @pytest.mark.asyncio
    async def test_parses_all_fields(self, api):
        api._core_api.get_variable.return_value = DEVICE_INFO_DATA
        result = await api.get_device_info()
        assert result.name == "TL-SG108PE"
        assert result.mac == "AA:BB:CC:DD:EE:FF"
        assert result.ip == "192.168.1.10"
        assert result.netmask == "255.255.255.0"
        assert result.gateway == "192.168.1.1"
        assert result.firmware == "1.0.6 Build 20221208"
        assert result.hardware == "TL-SG108PE 5.0"

    @pytest.mark.asyncio
    async def test_returns_none_for_multi_element_arrays(self, api):
        # Device returns wrong array length — field should be None
        api._core_api.get_variable.return_value = {
            "descriStr": ["name1", "name2"],  # len != 1
            "macStr": ["AA:BB:CC:DD:EE:FF"],
        }
        result = await api.get_device_info()
        assert result.name is None
        assert result.mac == "AA:BB:CC:DD:EE:FF"


# ---------------------------------------------------------------------------
# get_port_poe_states
# ---------------------------------------------------------------------------

class TestGetPortPoeStates:
    @pytest.mark.asyncio
    async def test_returns_empty_when_feature_unavailable(self, api):
        api._features.is_available.return_value = False
        result = await api.get_port_poe_states()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_data_none(self, api):
        api._core_api.get_variables.return_value = None
        result = await api.get_port_poe_states()
        assert result == []

    @pytest.mark.asyncio
    async def test_parses_port_count(self, api):
        api._core_api.get_variables.return_value = POE_PORT_DATA
        result = await api.get_port_poe_states()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_enabled_flag_parsed(self, api):
        api._core_api.get_variables.return_value = POE_PORT_DATA
        result = await api.get_port_poe_states()
        assert result[0].enabled is True   # state[0] == 1
        assert result[1].enabled is False  # state[1] == 0

    @pytest.mark.asyncio
    async def test_priority_parsed(self, api):
        api._core_api.get_variables.return_value = POE_PORT_DATA
        result = await api.get_port_poe_states()
        assert result[0].priority == PoePriority.HIGH
        assert result[1].priority == PoePriority.LOW

    @pytest.mark.asyncio
    async def test_power_limit_enum_parsed(self, api):
        api._core_api.get_variables.return_value = POE_PORT_DATA
        result = await api.get_port_poe_states()
        assert result[0].power_limit == PoePowerLimit.AUTO   # 330 → enum
        assert result[1].power_limit == PoePowerLimit.CLASS_1  # 40 → enum

    @pytest.mark.asyncio
    async def test_power_scaled_by_ten(self, api):
        api._core_api.get_variables.return_value = POE_PORT_DATA
        result = await api.get_port_poe_states()
        assert result[0].power == 15.0    # 150 / 10
        assert result[0].voltage == 48.0  # 480 / 10

    @pytest.mark.asyncio
    async def test_pd_class_parsed(self, api):
        api._core_api.get_variables.return_value = POE_PORT_DATA
        result = await api.get_port_poe_states()
        assert result[0].pd_class == PoeClass.CLASS_1  # pdclass[0] == 40
        assert result[1].pd_class == PoeClass.CLASS_0  # pdclass[1] == 330

    @pytest.mark.asyncio
    async def test_power_status_parsed(self, api):
        api._core_api.get_variables.return_value = POE_PORT_DATA
        result = await api.get_port_poe_states()
        assert result[0].power_status == PoePowerStatus.ON   # 2
        assert result[1].power_status == PoePowerStatus.OFF  # 0
