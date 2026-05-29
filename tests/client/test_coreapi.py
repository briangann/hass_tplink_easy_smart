"""Tests for coreapi.py pure parsing functions."""

import pytest

from custom_components.tplink_easy_smart.client.coreapi import (
    VariableType,
    _convert_value,
    _get_variable,
    _get_variables,
    _to_dict,
    _to_list,
)


# ---------------------------------------------------------------------------
# Fixtures — realistic HTML pages as returned by TP-Link device web UI
# ---------------------------------------------------------------------------

def _make_page(*var_lines: str) -> str:
    """Wrap variable declarations in a minimal TP-Link-style HTML page."""
    vars_block = "\n".join(var_lines)
    return f"<html><body><script>\n{vars_block}\n</script></body></html>"


PAGE_PORT_STATE = _make_page(
    "var max_port_num = 8;",
    "var all_info = {state: new Array(1,1,0,1,0,0,0,0), spd_cfg: new Array(1,1,1,1,1,1,1,1), spd_act: new Array(6,6,0,6,0,0,0,0), fc_cfg: new Array(0,0,0,0,0,0,0,0), fc_act: new Array(0,0,0,0,0,0,0,0)};",
    "var logonInfo = '0';",
)

PAGE_NO_SCRIPT = "<html><body>no script here</body></html>"

PAGE_EMPTY_SCRIPT = "<html><body><script></script></body></html>"

PAGE_QUOTED_STRING = _make_page("var name = 'SG108PE';")

PAGE_MULTI = _make_page(
    "var foo = 42;",
    "var bar = 'hello';",
    "var baz = new Array(1,2,3);",
)


# ---------------------------------------------------------------------------
# _get_variables
# ---------------------------------------------------------------------------

class TestGetVariables:
    def test_none_returns_empty(self):
        assert _get_variables(None) == {}

    def test_empty_string_returns_empty(self):
        assert _get_variables("") == {}

    def test_no_script_tag_returns_empty(self):
        assert _get_variables(PAGE_NO_SCRIPT) == {}

    def test_empty_script_tag_returns_empty(self):
        assert _get_variables(PAGE_EMPTY_SCRIPT) == {}

    def test_extracts_integer_variable(self):
        page = _make_page("var max_port_num = 8;")
        result = _get_variables(page)
        assert result["max_port_num"] == "8"

    def test_extracts_quoted_string_variable(self):
        result = _get_variables(PAGE_QUOTED_STRING)
        assert result["name"] == "'SG108PE'"

    def test_extracts_multiple_variables(self):
        result = _get_variables(PAGE_MULTI)
        assert "foo" in result
        assert "bar" in result
        assert "baz" in result

    def test_extracts_dict_variable_raw(self):
        result = _get_variables(PAGE_PORT_STATE)
        assert "all_info" in result
        assert "max_port_num" in result

    def test_variable_names_alphanumeric_underscore(self):
        page = _make_page("var port_1_state = 1;")
        result = _get_variables(page)
        assert "port_1_state" in result


# ---------------------------------------------------------------------------
# _to_list
# ---------------------------------------------------------------------------

class TestToList:
    def test_simple_integers(self):
        assert list(_to_list("new Array(1,2,3)")) == ["1", "2", "3"]

    def test_quoted_strings(self):
        result = list(_to_list('new Array("a","b","c")'))
        assert result == ["a", "b", "c"]

    def test_single_element(self):
        assert list(_to_list("new Array(42)")) == ["42"]

    def test_no_match_returns_empty(self):
        assert list(_to_list("not an array")) == []

    def test_empty_string_returns_empty(self):
        assert list(_to_list("")) == []

    def test_strips_whitespace(self):
        result = list(_to_list("new Array( 1 , 2 , 3 )"))
        assert result == ["1", "2", "3"]

    def test_mixed_values(self):
        result = list(_to_list('new Array(0,1,"auto")'))
        assert result == ["0", "1", "auto"]


# ---------------------------------------------------------------------------
# _to_dict
# ---------------------------------------------------------------------------

class TestToDict:
    def test_json5_unquoted_keys(self):
        result = _to_dict("{state: 1, name: 'test'}")
        assert result == {"state": 1, "name": "test"}

    def test_nested_arrays(self):
        result = _to_dict("{items: [1, 2, 3]}")
        assert result is not None
        assert result["items"] == [1, 2, 3]

    def test_empty_string_returns_none(self):
        assert _to_dict("") is None

    def test_standard_json(self):
        result = _to_dict('{"key": "value"}')
        assert result == {"key": "value"}

    def test_returns_dict_type(self):
        result = _to_dict("{x: 1}")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# _convert_value
# ---------------------------------------------------------------------------

class TestConvertValue:
    def test_none_returns_none(self):
        assert _convert_value(None, VariableType.Str) is None
        assert _convert_value(None, VariableType.Int) is None
        assert _convert_value(None, VariableType.List) is None
        assert _convert_value(None, VariableType.Dict) is None

    def test_str_strips_single_quotes(self):
        assert _convert_value("'hello'", VariableType.Str) == "hello"

    def test_str_strips_double_quotes(self):
        assert _convert_value('"hello"', VariableType.Str) == "hello"

    def test_str_no_quotes(self):
        assert _convert_value("hello", VariableType.Str) == "hello"

    def test_int_valid(self):
        assert _convert_value("8", VariableType.Int) == 8

    def test_int_zero(self):
        assert _convert_value("0", VariableType.Int) == 0

    def test_int_invalid_raises(self):
        with pytest.raises(ValueError):
            _convert_value("not_a_number", VariableType.Int)

    def test_list_parses_array(self):
        result = _convert_value("new Array(1,2,3)", VariableType.List)
        assert result == ["1", "2", "3"]

    def test_list_no_match_returns_empty(self):
        result = _convert_value("invalid", VariableType.List)
        assert result == []

    def test_dict_parses_object(self):
        result = _convert_value("{state: 1}", VariableType.Dict)
        assert isinstance(result, dict)
        assert result["state"] == 1

    def test_dict_empty_string_returns_none(self):
        assert _convert_value("", VariableType.Dict) is None


# ---------------------------------------------------------------------------
# _get_variable
# ---------------------------------------------------------------------------

class TestGetVariable:
    def test_extracts_int(self):
        result = _get_variable(PAGE_PORT_STATE, "max_port_num", VariableType.Int)
        assert result == 8

    def test_extracts_str(self):
        result = _get_variable(PAGE_QUOTED_STRING, "name", VariableType.Str)
        assert result == "SG108PE"

    def test_missing_variable_returns_none(self):
        result = _get_variable(PAGE_PORT_STATE, "nonexistent", VariableType.Int)
        assert result is None

    def test_no_script_returns_none(self):
        result = _get_variable(PAGE_NO_SCRIPT, "max_port_num", VariableType.Int)
        assert result is None

    def test_logon_info_str(self):
        result = _get_variable(PAGE_PORT_STATE, "logonInfo", VariableType.Str)
        assert result == "0"
