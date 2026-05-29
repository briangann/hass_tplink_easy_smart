# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Type checking

There is no test suite. The primary correctness tool is pyright. Run it against the whole integration:

```bash
pyright custom_components/tplink_easy_smart/
```

`pyrightconfig.json` is gitignored (machine-specific). The repo ships a template pointing to `.venv` in the project root — just create the venv:

```bash
uv venv --python 3.14
git clone --depth 1 --branch 2026.5.4 https://github.com/home-assistant/core.git /tmp/ha-core
uv pip install --no-deps /tmp/ha-core
uv pip install aiohttp voluptuous json5 pyright
```

HA 2026.x requires Python 3.14+. `--no-deps` skips HA's large runtime dependency tree — only the HA source is needed for type checking.

## Architecture

The code has two distinct layers: a device client and the HA integration layer.

### Client layer (`custom_components/tplink_easy_smart/client/`)

**`coreapi.py` — raw HTTP**
`TpLinkWebApi` owns the aiohttp session, handles auth (cookie-based), and does GET/POST. The TP-Link switch web UI returns HTML pages with embedded JavaScript variable assignments (`var foo = value;`), not JSON. The code extracts these with regex. Dict-type variables are parsed with `json5` (the device uses JS object syntax with unquoted keys). `VariableValue = str | int | list[str] | dict[str, Any]` — callers must narrow with `isinstance()` before use.

**`tplink_api.py` — typed API**
`TpLinkApi` sits on top of `TpLinkWebApi` and returns typed dataclasses (`PortState`, `PortPoeState`, `PortStatistics`, etc.). It also checks feature availability before calls that require optional device capabilities.

**`utils.py` — feature detection**
`TpLinkFeaturesDetector` probes specific endpoints (`PoeConfigRpm.htm`, `PortStatisticsRpm.htm`) to determine what the connected switch supports. Detection is lazy and runs once.

**`classes.py` — dataclasses**
All device entity types live here. `TpLinkSystemInfo`, `PortState`, `PortPoeState`, `PortStatistics`, `PoeState`, and the various enums (`PortSpeed`, `PoePriority`, etc.).

### HA integration layer

**`update_coordinator.py` — `TpLinkDataUpdateCoordinator`**
Inherits `DataUpdateCoordinator[None]`. Polls the API on a configurable interval (default 30s). Caches all device state internally and notifies HA entities via the coordinator pattern. Feature availability (`_feature_poe`, `_feature_stats`) is detected on the first update cycle and stored as booleans — all subsequent cycles use sync bool checks, not async feature probes.

**Entity files (`sensor.py`, `binary_sensor.py`, `switch.py`)**
All entities read exclusively from the coordinator cache — they never call the API directly. Entity descriptions use `@dataclass(frozen=True)` to satisfy HA's frozen `EntityDescription` base class. The `name` field is computed and passed at construction time (not in `__post_init__`).

**`displayed_values.py`**
Mapping dicts from enum values to display strings. Used by binary sensors to render port speed, PoE class, power status, etc.

**`services.py`**
HA service handlers for `set_general_poe_limit` and `set_port_poe_settings`. Registered once per HA instance (not per config entry) via an instance count guard. Uses `verify_domain_control(hass, DOMAIN)` as a decorator.

### Key invariants

- `get_variables()` returns `dict[str, VariableValue | None] | None` — always check for `None` response and use `isinstance(value, dict)` / `isinstance(value, int)` before use, not truthiness.
- `get_switch_info()` returns `TpLinkSystemInfo | None` at any time before the first successful poll — all callers must guard.
- Port array data from the device may have fewer entries than `max_port_num` indicates — loop with a bounds break, as `get_port_statistics` and `get_port_states` do.
- `manifest.json` lists `json5==0.9.10` as a requirement; the dev venv has a newer version. Update the manifest when bumping.
