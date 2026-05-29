"""Tests for utils.py TpLinkFeaturesDetector."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.tplink_easy_smart.client.coreapi import (
    ApiCallError,
    APICALL_ERRCODE_DISCONNECTED,
    APICALL_ERRCAT_DISCONNECTED,
)
from custom_components.tplink_easy_smart.client.const import FEATURE_POE, FEATURE_STATS
from custom_components.tplink_easy_smart.client.utils import TpLinkFeaturesDetector


@pytest.fixture
def core_api():
    mock = MagicMock()
    mock.get_variables = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def detector(core_api):
    return TpLinkFeaturesDetector(core_api)


# ---------------------------------------------------------------------------
# is_available (sync, reads cached set)
# ---------------------------------------------------------------------------

class TestIsAvailable:
    def test_false_before_update(self, detector):
        assert detector.is_available(FEATURE_POE) is False
        assert detector.is_available(FEATURE_STATS) is False

    def test_true_after_direct_add(self, detector):
        detector._available_features.add(FEATURE_POE)
        assert detector.is_available(FEATURE_POE) is True
        assert detector.is_available(FEATURE_STATS) is False

    def test_unknown_feature_returns_false(self, detector):
        assert detector.is_available("feature_nonexistent") is False


# ---------------------------------------------------------------------------
# _is_poe_available
# ---------------------------------------------------------------------------

class TestIsPoeAvailable:
    async def test_false_when_data_none(self, detector, core_api):
        core_api.get_variables.return_value = None
        result = await detector._is_poe_available()
        assert result is False

    async def test_false_when_portconfig_missing(self, detector, core_api):
        core_api.get_variables.return_value = {"poe_port_num": 4}
        result = await detector._is_poe_available()
        assert result is False

    async def test_false_when_port_num_zero(self, detector, core_api):
        core_api.get_variables.return_value = {
            "portConfig": {"state": [1]},
            "poe_port_num": 0,
        }
        result = await detector._is_poe_available()
        assert result is False

    async def test_false_when_port_num_not_int(self, detector, core_api):
        core_api.get_variables.return_value = {
            "portConfig": {"state": [1]},
            "poe_port_num": None,
        }
        result = await detector._is_poe_available()
        assert result is False

    async def test_true_when_portconfig_and_positive_port_num(self, detector, core_api):
        core_api.get_variables.return_value = {
            "portConfig": {"state": [1, 1, 1, 1]},
            "poe_port_num": 4,
        }
        result = await detector._is_poe_available()
        assert result is True

    async def test_false_on_disconnected_error(self, detector, core_api):
        core_api.get_variables.side_effect = ApiCallError(
            "disconnected", APICALL_ERRCODE_DISCONNECTED, APICALL_ERRCAT_DISCONNECTED
        )
        result = await detector._is_poe_available()
        assert result is False

    async def test_reraises_non_disconnected_error(self, detector, core_api):
        core_api.get_variables.side_effect = ApiCallError(
            "request error", -3, "request_error"
        )
        with pytest.raises(ApiCallError):
            await detector._is_poe_available()


# ---------------------------------------------------------------------------
# _is_stats_available
# ---------------------------------------------------------------------------

class TestIsStatsAvailable:
    async def test_false_when_data_none(self, detector, core_api):
        core_api.get_variables.return_value = None
        result = await detector._is_stats_available()
        assert result is False

    async def test_false_when_all_info_missing(self, detector, core_api):
        core_api.get_variables.return_value = {"max_port_num": 8}
        result = await detector._is_stats_available()
        assert result is False

    async def test_false_when_max_port_num_zero(self, detector, core_api):
        core_api.get_variables.return_value = {
            "all_info": {"pkts": []},
            "max_port_num": 0,
        }
        result = await detector._is_stats_available()
        assert result is False

    async def test_true_when_all_info_and_positive_port_num(self, detector, core_api):
        core_api.get_variables.return_value = {
            "all_info": {"pkts": [1, 0, 2, 0]},
            "max_port_num": 8,
        }
        result = await detector._is_stats_available()
        assert result is True

    async def test_false_on_disconnected_error(self, detector, core_api):
        core_api.get_variables.side_effect = ApiCallError(
            "disconnected", APICALL_ERRCODE_DISCONNECTED, APICALL_ERRCAT_DISCONNECTED
        )
        result = await detector._is_stats_available()
        assert result is False


# ---------------------------------------------------------------------------
# update — populates _available_features
# ---------------------------------------------------------------------------

class TestUpdate:
    async def test_adds_poe_when_available(self, detector, core_api):
        async def get_variables(url, variables, **kwargs):
            if "PoeConfig" in url:
                return {"portConfig": {"state": [1]}, "poe_port_num": 4}
            return None

        core_api.get_variables.side_effect = get_variables
        await detector.update()
        assert detector.is_available(FEATURE_POE) is True
        assert detector.is_available(FEATURE_STATS) is False

    async def test_adds_stats_when_available(self, detector, core_api):
        async def get_variables(url, variables, **kwargs):
            if "PortStatistics" in url:
                return {"all_info": {"pkts": []}, "max_port_num": 8}
            return None

        core_api.get_variables.side_effect = get_variables
        await detector.update()
        assert detector.is_available(FEATURE_STATS) is True
        assert detector.is_available(FEATURE_POE) is False

    async def test_adds_both_when_both_available(self, detector, core_api):
        async def get_variables(url, variables, **kwargs):
            if "PoeConfig" in url:
                return {"portConfig": {"state": [1]}, "poe_port_num": 4}
            if "PortStatistics" in url:
                return {"all_info": {"pkts": []}, "max_port_num": 8}
            return None

        core_api.get_variables.side_effect = get_variables
        await detector.update()
        assert detector.is_available(FEATURE_POE) is True
        assert detector.is_available(FEATURE_STATS) is True

    async def test_adds_nothing_when_neither_available(self, detector, core_api):
        core_api.get_variables.return_value = None
        await detector.update()
        assert detector.is_available(FEATURE_POE) is False
        assert detector.is_available(FEATURE_STATS) is False
