# eDisGo-only workflow with `run_edisgo`

This document describes the new eDisGo-only workflow that replaces the
hand-rolled per-grid task dispatcher in `EDisGoNetworks.run_edisgo()`
with a single delegation to `edisgo.run.run_edisgo()`.

## Why the change

Historically, eGo had a long linear `run_edisgo(mv_grid_id)` method
(~1200 lines) that hard-coded the per-grid task sequence (setup grid,
import generators, set time series, reinforce, save). Every new
analysis required adding another branch into that dispatcher.

eDisGo now exposes its own runner — `edisgo.run.run_edisgo(config)` —
modeled on the way eTraGo exposes `run_etrago(args)`. The per-grid
task list lives in YAML presets inside eDisGo. eGo only orchestrates
multi-grid execution (clustering, parallelization, results
aggregation) and delegates the per-grid pipeline.

## Architecture

```
eGo()
 └─ EDisGoNetworks._run_edisgo_pool()      # multi-grid loop, kept
     └─ parallelizer / Pool                 # kept
         └─ run_edisgo(mv_grid_id)          # weiche
             ├─ if self._preset:            # NEW path
             │     └─ _run_one_grid_via_runner(mv_grid_id)
             │         ├─ cfg = _build_run_edisgo_config(mv_grid_id)
             │         └─ edisgo.run.run_edisgo(cfg) -> EDisGo
             └─ else:                       # legacy path (eTraGo-coupled)
                   └─ existing _run_edisgo_task_* methods
```

The legacy path is unchanged; it stays for the eTraGo→eDisGo coupling
where eGo passes a disaggregated eTraGo network into the per-grid
tasks (`2_specs_overlying_grid`, `4_optimisation`).

## The eDisGo runner

Lives in `edisgo/run/`:

| File | Role |
|------|------|
| `runner.py` | Public `run_edisgo(config) -> EDisGo`. Iterates stages, calls registered tasks. |
| `registry.py` | `@register_task("name")` decorator; tasks live in `tasks/`. |
| `config.py` | `load_config()`: parse YAML/JSON/dict, resolve `extends:`, normalize stages. |
| `context.py` | `RunContext`: shared state (DB engine, results dir, scenario, flags). |
| `validator.py` | Static validation of pipeline order & required dependencies. |
| `tasks/grid.py` | `setup_grid`, `load_from_base`. |
| `tasks/io.py` | `save`, `load_charging_from_files` (stub). |
| `tasks/timeseries.py` | `worst_case_ts`, `oedb_ts`, `reactive_power`, `apply_heat_pump_strategy`. |
| `tasks/flex.py` | `import_heat_pumps`, `import_home_batteries`, `import_dsm`, `import_electromobility`. |
| `tasks/analysis.py` | `analyze`, `check_integrity`, `reinforce`, `base_reinforce`, `optimize`. |
| `presets/*.yaml` | Bundled workflow presets. |

### Bundled presets

| Preset | Pipeline (compact) |
|--------|--------------------|
| `basic` | setup_grid → worst_case_ts → reactive_power → check_integrity → reinforce → save |
| `uc1_loads_worst_case` | setup_grid → base_reinforce → import_heat_pumps → import_home_batteries → import_dsm → import_electromobility(dumb) → worst_case_ts → reactive_power → reinforce → save |
| `uc2_flex_opf` | …same imports… → oedb_ts(168h) → apply_heat_pump_strategy → reactive_power → check_integrity → optimize → reinforce → save |
| `uc3_oedb_ts` | …same imports… → oedb_ts(168h) → apply_heat_pump_strategy → reactive_power → reinforce → save |
| `r4mu_base_and_scenario` | two-stage: base reinforce + scenario stage with `load_from: base` |

### Calling the runner directly (without eGo)

```python
from edisgo.run import run_edisgo

# Path to a YAML preset:
edisgo = run_edisgo("uc1_loads_worst_case")          # bundled preset by name
edisgo = run_edisgo("/path/to/my_custom.yaml")       # custom file

# Or as a dict (extends a preset, overrides specific keys):
edisgo = run_edisgo({
    "extends": "uc1_loads_worst_case",
    "scenario": "eGon2035",
    "grid": {"ding0_path": "/home/.../ding0_grids/30879"},
    "results": {"directory": "/tmp/uc1_30879"},
    "database": {
        "host": "localhost", "port": 59510,
        "user": "egon", "password": "data",
        "database_name": "egon-data",
    },
})

print(edisgo.results.grid_expansion_costs)
```

`run_edisgo` returns a single `EDisGo` instance after the final stage.

## Using it from eGo

The integration is trivial: set `eDisGo.preset` in the scenario JSON.
eGo then forwards every per-grid call to `run_edisgo`.

### Minimal scenario JSON (eDisGo-only)

```json
{
  "eGo": {
    "eTraGo": false,
    "eDisGo": true,
    "csv_import_eTraGo": false,
    "csv_import_eDisGo": false,
    "random_seed": 42
  },
  "eTraGo": {
    "scn_name": "eGon2035",
    "extendable": []
  },
  "eDisGo": {
    "preset": "uc1_loads_worst_case",

    "grid_path": "/home/gurobi/.ding0/.../ding0_grids",
    "results":   "/storage/JoDa/results/uc1",
    "choice_mode": "manual",
    "manual_grids": [30879],

    "parallelization": false,
    "max_workers": 4,
    "max_calc_time": 2.0,
    "cluster_attributes": [],
    "n_clusters": 2,
    "only_cluster": false,
    "max_cos_phi_renewable": 0.9,
    "solver": "gurobi",
    "gridversion": null,
    "tasks": []
  },
  "database": {
    "database_name": "egon-data",
    "host": "localhost", "port": "59510",
    "user": "egon", "password": "data"
  },
  "ssh": { "enabled": false }
}
```

`tasks` is ignored when `preset` is set. The pipeline comes from the
preset YAML inside eDisGo.

### Field overrides built by eGo

For each MV grid, `EDisGoNetworks._build_run_edisgo_config(mv_grid_id)`
constructs:

```python
{
  "extends": <preset>,
  "scenario": <eTraGo.scn_name or "eGon2035">,
  "grid":    {"ding0_path": "<grid_path>/<mv_grid_id>"},
  "results": {"directory": "<results>/<mv_grid_id>"},
  "database": {<database block>, "ssh": {<ssh block>}},
}
```

`extends` makes `run_edisgo` load the preset YAML and merge the
overrides on top — so all pipeline tasks come from the preset, but
paths and DB credentials are per-grid / per-installation.

### Running it

```bash
cd /storage/JoDa/ego/eGo/ego
ln -sf scenario_setting_uc1_loads_worst_case.json scenario_setting.json
/storage/JoDa/ego/.venv310ego/bin/python appl.py
```

Single-grid smoke test without the full `eGo()` bootstrap (skips eTraGo
boilerplate, useful for debugging):

```python
import json
from ego.tools.edisgo_integration import EDisGoNetworks

cfg = json.load(open("scenario_setting_uc1_loads_worst_case.json"))
cfg["eDisGo"]["choice_mode"] = "manual"
cfg["eDisGo"]["manual_grids"] = [30879]
cfg["eDisGo"]["parallelization"] = False

nets = EDisGoNetworks(json_file=cfg, etrago_network=None)
print(nets._edisgo_grids[30879])
```

### Multi-grid

For a real multi-grid run, set:

```json
"choice_mode": "all",          // or "cluster" with n_clusters
"parallelization": true,
"max_workers": 4
```

eGo's existing `_run_edisgo_pool()` distributes grids across worker
processes; each worker calls `_run_one_grid_via_runner` independently.
Per-grid result directories land under `results/<mv_grid_id>/`.

## Switching to a different preset

Three options:

1. **Bundled name** — change `eDisGo.preset` to one of `basic`,
   `uc1_loads_worst_case`, `uc2_flex_opf`, `uc3_oedb_ts`,
   `r4mu_base_and_scenario`.
2. **Custom YAML** — point `preset` at a path to your own YAML. The
   loader auto-detects path vs bundled name.
3. **Inline override in eGo** — modify `_build_run_edisgo_config` to
   inject step-specific overrides via the runner's
   `{{params.KEY}}` substitution.

## Coexistence with the legacy eTraGo path

Set `eDisGo.preset = null` (or omit the field) and provide a `tasks`
list with the legacy task names (`1_setup_grid`,
`2_specs_overlying_grid`, …). EDisGoNetworks will then use the
unchanged old code path that consumes `etrago_network` from the eGo
side. Both paths live side by side; `preset` is the only switch.

## Limitations & known issues

- `import_home_batteries` in eDisGo currently routes to OEP
  (openenergyplatform.org) instead of the configured local
  egon-data engine. Crashes with
  `requests.exceptions.InvalidJSONError: Out of range float values are
  not JSON compliant`. Fix is on the eDisGo side (`storage_import.py`
  needs to honor `ctx.engine`).
- `load_charging_from_files` task in eDisGo's runner is a stub
  (`NotImplementedError`). Needed for the r4mu scenario stage —
  port the implementation from the legacy
  `_run_edisgo_task_load_charging_from_files` in
  `edisgo_integration.py`.
- Hard import `from etrago import Etrago, run_etrago` in
  `ego/tools/io.py:38` — eGo will not start if eTraGo is uninstalled
  (independent of `preset`). Make optional in a follow-up.

## Reference: relevant commits on `features/#171-update-integration-of-edisgo`

```
0cdf956  Delegate per-grid eDisGo workflow to edisgo.run.run_edisgo
b0b49f1  Make eTraGo optional in EDisGoNetworks
4274c76  Guard io.py against missing eTraGo results
5671aa4  Allow eDisGo to run without eTraGo results
```
