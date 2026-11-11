"""
Checks that the example scenario settings shipped with eGo can be used.

The examples are read from the installed eGo package, so the tests also check
that they are packaged. No solver is needed. eGo creates its database engine,
which is the OpenEnergy Platform unless an egon-data configuration exists, but
the tests do not query it.
"""
import json
import os

import geopandas as gpd
import pandas as pd
import pytest

from edisgo.run.config import load_config
from edisgo.run.validator import validate
from etrago.appl import args as etrago_default_args
from pypsa import Network as PyPSANetwork
from shapely.geometry import box

import ego

from ego.tools.edisgo_integration import EDisGoNetworks
from ego.tools.interface import ETraGoMinimalData, get_etrago_results_per_bus
from ego.tools.io import eGo
from ego.tools.utilities import get_scenario_setting

EXAMPLE_DIR = os.path.dirname(ego.__file__)
# listed explicitly, so a missing file fails instead of being skipped
EXAMPLES = [
    "eGo_load_eTraGo_run_eDisGo.json",
    "eGo_minimal_example.json",
    "eGo_with_focus_region.json",
]


def _write_scenario(tmp_path, example, **sections):
    """
    Copy an example scenario setting to `tmp_path`, with the results written
    to `tmp_path` and the given sections updated, e.g. ``eGo={...}``.
    """
    with open(os.path.join(EXAMPLE_DIR, example)) as f:
        scenario = json.load(f)
    scenario["eGo"]["result_export_path"] = str(tmp_path / "results")
    for name, settings in sections.items():
        scenario[name].update(settings)

    jsonpath = tmp_path / example
    with open(jsonpath, "w") as f:
        json.dump(scenario, f)
    return str(jsonpath)


def _write_etrago_results(path, focus_region):
    """
    Write the eTraGo test network to `path` in the layout eTraGo exports its
    results in, with a focus region given as file.
    """
    network = PyPSANetwork(pytest.etrago_test_network_1_path)
    path.mkdir()
    network.export_to_csv_folder(str(path / "non_linear_powerflow"))
    network.export_to_netcdf(str(path / "disaggregated_network.nc"))

    args = json.loads(json.dumps(etrago_default_args))
    args["pf_post_lopf"]["active"] = True
    args["method"]["market_optimization"]["active"] = False
    args["spatial_disaggregation"] = "uniform"
    args["network_clustering"]["method"]["focus_region"] = str(focus_region)
    with open(path / "args.json", "w") as f:
        json.dump(args, f)
    return network


def _edisgo_config(scenario, mv_grid_id):
    """eDisGo run configuration eGo builds from the scenario setting."""
    networks = EDisGoNetworks.__new__(EDisGoNetworks)
    networks._json_file = scenario
    networks._set_scenario_settings()
    return load_config(networks._build_run_edisgo_config(mv_grid_id))


def _assert_equal(result, expected):
    if isinstance(expected, pd.DataFrame):
        pd.testing.assert_frame_equal(
            result, expected, check_names=False, check_freq=False
        )
    elif isinstance(expected, pd.Series):
        pd.testing.assert_series_equal(
            result, expected, check_names=False, check_freq=False
        )
    elif isinstance(expected, pd.Index):
        pd.testing.assert_index_equal(result, expected, exact=False)
    else:
        assert result == expected


@pytest.mark.parametrize("example", EXAMPLES)
def test_example_scenario_settings_load(tmp_path, example):
    """The example loads and eDisGo accepts the configuration eGo builds."""
    scenario = get_scenario_setting(_write_scenario(tmp_path, example))

    assert scenario["eTraGo"]["scn_name"] == "eGon2035"
    assert (tmp_path / "results" / "config.json").is_file()
    validate(_edisgo_config(scenario, mv_grid_id=32377))


@pytest.mark.usefixtures("no_mv_lv_renewable_capacities")
def test_run_with_imported_etrago_results(tmp_path):
    """
    eGo imports eTraGo results, selects MV grid 0 and builds the input for
    eDisGo, which is the same as for the original eTraGo network. eDisGo
    itself is not run, as it needs the MV grids and a solver.
    """
    focus_region = tmp_path / "focus_region.geojson"
    gpd.GeoDataFrame(geometry=[box(9, 54, 10, 55)], crs=4326).to_file(focus_region)
    etrago_results = tmp_path / "etrago_results"
    network = _write_etrago_results(etrago_results, focus_region)
    jsonpath = _write_scenario(
        tmp_path,
        "eGo_load_eTraGo_run_eDisGo.json",
        eGo={"csv_import_eTraGo": str(etrago_results), "eDisGo": False},
        eDisGo={"choice_mode": "manual", "manual_grids": [0]},
    )

    ego = eGo(jsonpath=jsonpath)
    ego.run()

    assert ego.focus_region.geometry.iloc[0].equals(box(9, 54, 10, 55))
    assert ego.mvlv_grid_choice["the_selected_network_id"].tolist() == [0]
    assert ego.edisgo is None
    # eGo continues with the settings of the imported eTraGo run
    assert ego._json_file["eTraGo"]["spatial_disaggregation"] == "uniform"

    results = get_etrago_results_per_bus(
        0,
        ETraGoMinimalData(ego.etrago.disaggregated_network, ego._json_file),
        pf_post_lopf=True,
        max_cos_phi_ren=False,
    )
    expected = get_etrago_results_per_bus(
        0,
        ETraGoMinimalData(network, ego._json_file),
        pf_post_lopf=True,
        max_cos_phi_ren=False,
    )
    assert results.keys() == expected.keys()
    for key in expected:
        _assert_equal(results[key], expected[key])

    validate(_edisgo_config(ego._json_file, mv_grid_id=0))
