"""Tests for classes.py enum try_parse methods."""

from custom_components.tplink_easy_smart.client.classes import (
    PoeClass,
    PoePowerLimit,
    PoePowerStatus,
    PoePriority,
    PortSpeed,
    PortStatistics,
    TpLinkSystemInfo,
)


class TestPoePriorityTryParse:
    def test_valid_values_return_enum(self):
        assert PoePriority.try_parse(0) == PoePriority.HIGH
        assert PoePriority.try_parse(1) == PoePriority.MIDDLE
        assert PoePriority.try_parse(2) == PoePriority.LOW

    def test_invalid_value_returns_none(self):
        assert PoePriority.try_parse(99) is None
        assert PoePriority.try_parse(-1) is None

    def test_returns_correct_type(self):
        result = PoePriority.try_parse(0)
        assert isinstance(result, PoePriority)


class TestPoePowerLimitTryParse:
    def test_valid_values_return_enum(self):
        assert PoePowerLimit.try_parse(330) == PoePowerLimit.AUTO
        assert PoePowerLimit.try_parse(40) == PoePowerLimit.CLASS_1
        assert PoePowerLimit.try_parse(70) == PoePowerLimit.CLASS_2
        assert PoePowerLimit.try_parse(154) == PoePowerLimit.CLASS_3
        assert PoePowerLimit.try_parse(300) == PoePowerLimit.CLASS_4

    def test_invalid_value_returns_none(self):
        assert PoePowerLimit.try_parse(0) is None
        assert PoePowerLimit.try_parse(999) is None

    def test_returns_correct_type(self):
        result = PoePowerLimit.try_parse(330)
        assert isinstance(result, PoePowerLimit)


class TestPoeClassTryParse:
    def test_valid_values_return_enum(self):
        assert PoeClass.try_parse(330) == PoeClass.CLASS_0
        assert PoeClass.try_parse(40) == PoeClass.CLASS_1
        assert PoeClass.try_parse(70) == PoeClass.CLASS_2
        assert PoeClass.try_parse(154) == PoeClass.CLASS_3
        assert PoeClass.try_parse(300) == PoeClass.CLASS_4

    def test_invalid_value_returns_none(self):
        assert PoeClass.try_parse(0) is None
        assert PoeClass.try_parse(999) is None

    def test_returns_correct_type(self):
        result = PoeClass.try_parse(40)
        assert isinstance(result, PoeClass)


class TestPoePowerStatusTryParse:
    def test_valid_values_return_enum(self):
        assert PoePowerStatus.try_parse(0) == PoePowerStatus.OFF
        assert PoePowerStatus.try_parse(1) == PoePowerStatus.TURNING_ON
        assert PoePowerStatus.try_parse(2) == PoePowerStatus.ON
        assert PoePowerStatus.try_parse(9) == PoePowerStatus.OVERTEMPERATURE

    def test_all_members_parseable(self):
        for member in PoePowerStatus:
            assert PoePowerStatus.try_parse(member.value) == member

    def test_invalid_value_returns_none(self):
        assert PoePowerStatus.try_parse(99) is None
        assert PoePowerStatus.try_parse(-1) is None


class TestPortSpeedValues:
    def test_link_down_is_zero(self):
        assert PortSpeed.LINK_DOWN == 0

    def test_auto_is_one(self):
        assert PortSpeed.AUTO == 1

    def test_gigabit_is_six(self):
        # device returns 6 for 1000MF
        assert PortSpeed.FULL_1000M == 6

    def test_all_members_int_comparable(self):
        for member in PortSpeed:
            assert isinstance(member.value, int)


class TestTpLinkSystemInfoDefaults:
    def test_all_fields_default_none(self):
        info = TpLinkSystemInfo()
        assert info.name is None
        assert info.mac is None
        assert info.ip is None
        assert info.netmask is None
        assert info.gateway is None
        assert info.firmware is None
        assert info.hardware is None

    def test_fields_assignable(self):
        info = TpLinkSystemInfo(name="Switch", mac="AA:BB:CC:DD:EE:FF")
        assert info.name == "Switch"
        assert info.mac == "AA:BB:CC:DD:EE:FF"


class TestPortStatisticsDataclass:
    def test_fields_stored(self):
        stats = PortStatistics(
            number=1,
            enabled=True,
            tx_good_pkts=100,
            tx_bad_pkts=0,
            rx_good_pkts=200,
            rx_bad_pkts=1,
        )
        assert stats.number == 1
        assert stats.enabled is True
        assert stats.tx_good_pkts == 100
        assert stats.rx_good_pkts == 200
        assert stats.rx_bad_pkts == 1
