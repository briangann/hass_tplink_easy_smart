"""Tests for displayed_values.py mapping dicts."""

from custom_components.tplink_easy_smart.client.classes import (
    PoeClass,
    PoePowerLimit,
    PoePowerStatus,
    PoePriority,
    PortSpeed,
)
from custom_components.tplink_easy_smart.displayed_values import (
    DISPLAYED_POE_CLASSES,
    DISPLAYED_POE_POWER_LIMITS,
    DISPLAYED_POE_POWER_STATUS,
    DISPLAYED_POE_PRIORITY,
    DISPLAYED_PORT_SPEED,
)


class TestDisplayedPortSpeed:
    def test_all_values_return_strings(self):
        for value in DISPLAYED_PORT_SPEED.values():
            assert isinstance(value, str)

    def test_no_duplicate_labels(self):
        labels = list(DISPLAYED_PORT_SPEED.values())
        assert len(labels) == len(set(labels))

    def test_known_speeds_present(self):
        assert PortSpeed.AUTO in DISPLAYED_PORT_SPEED
        assert PortSpeed.LINK_DOWN in DISPLAYED_PORT_SPEED
        assert PortSpeed.FULL_10M in DISPLAYED_PORT_SPEED
        assert PortSpeed.FULL_100M in DISPLAYED_PORT_SPEED
        assert PortSpeed.FULL_1000M in DISPLAYED_PORT_SPEED
        assert PortSpeed.HALF_10M in DISPLAYED_PORT_SPEED
        assert PortSpeed.HALF_100M in DISPLAYED_PORT_SPEED

    def test_unknown_speed_not_present(self):
        # UNKNOWN has no display string — callers get None from .get()
        assert PortSpeed.UNKNOWN not in DISPLAYED_PORT_SPEED

    def test_specific_labels(self):
        assert DISPLAYED_PORT_SPEED[PortSpeed.AUTO] == "Auto"
        assert DISPLAYED_PORT_SPEED[PortSpeed.LINK_DOWN] == "Link Down"
        assert DISPLAYED_PORT_SPEED[PortSpeed.FULL_1000M] == "1000MF"


class TestDisplayedPoePriority:
    def test_all_members_covered(self):
        for member in PoePriority:
            assert member in DISPLAYED_POE_PRIORITY

    def test_all_values_return_strings(self):
        for value in DISPLAYED_POE_PRIORITY.values():
            assert isinstance(value, str)

    def test_no_duplicate_labels(self):
        labels = list(DISPLAYED_POE_PRIORITY.values())
        assert len(labels) == len(set(labels))

    def test_specific_labels(self):
        assert DISPLAYED_POE_PRIORITY[PoePriority.HIGH] == "High"
        assert DISPLAYED_POE_PRIORITY[PoePriority.MIDDLE] == "Middle"
        assert DISPLAYED_POE_PRIORITY[PoePriority.LOW] == "Low"


class TestDisplayedPoePowerLimits:
    def test_all_members_covered(self):
        for member in PoePowerLimit:
            assert member in DISPLAYED_POE_POWER_LIMITS

    def test_all_values_return_strings(self):
        for value in DISPLAYED_POE_POWER_LIMITS.values():
            assert isinstance(value, str)

    def test_no_duplicate_labels(self):
        labels = list(DISPLAYED_POE_POWER_LIMITS.values())
        assert len(labels) == len(set(labels))

    def test_specific_labels(self):
        assert DISPLAYED_POE_POWER_LIMITS[PoePowerLimit.AUTO] == "Auto"
        assert DISPLAYED_POE_POWER_LIMITS[PoePowerLimit.CLASS_1] == "Class 1"
        assert DISPLAYED_POE_POWER_LIMITS[PoePowerLimit.CLASS_4] == "Class 4"


class TestDisplayedPoeClasses:
    def test_all_members_covered(self):
        for member in PoeClass:
            assert member in DISPLAYED_POE_CLASSES

    def test_all_values_return_strings(self):
        for value in DISPLAYED_POE_CLASSES.values():
            assert isinstance(value, str)

    def test_no_duplicate_labels(self):
        labels = list(DISPLAYED_POE_CLASSES.values())
        assert len(labels) == len(set(labels))

    def test_labels_match_class_number(self):
        # Regression: CLASS_1 was previously labelled "Class 2", CLASS_2 as "Class 3"
        assert DISPLAYED_POE_CLASSES[PoeClass.CLASS_0] == "Class 0"
        assert DISPLAYED_POE_CLASSES[PoeClass.CLASS_1] == "Class 1"
        assert DISPLAYED_POE_CLASSES[PoeClass.CLASS_2] == "Class 2"
        assert DISPLAYED_POE_CLASSES[PoeClass.CLASS_3] == "Class 3"
        assert DISPLAYED_POE_CLASSES[PoeClass.CLASS_4] == "Class 4"


class TestDisplayedPoePowerStatus:
    def test_all_members_covered(self):
        for member in PoePowerStatus:
            assert member in DISPLAYED_POE_POWER_STATUS

    def test_all_values_return_strings(self):
        for value in DISPLAYED_POE_POWER_STATUS.values():
            assert isinstance(value, str)

    def test_no_duplicate_labels(self):
        labels = list(DISPLAYED_POE_POWER_STATUS.values())
        assert len(labels) == len(set(labels))

    def test_specific_labels(self):
        assert DISPLAYED_POE_POWER_STATUS[PoePowerStatus.OFF] == "Off"
        assert DISPLAYED_POE_POWER_STATUS[PoePowerStatus.ON] == "On"
        assert DISPLAYED_POE_POWER_STATUS[PoePowerStatus.OVELOAD] == "Overload"
        assert DISPLAYED_POE_POWER_STATUS[PoePowerStatus.OVERTEMPERATURE] == "Overtemperature"
