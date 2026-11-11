import os

import pandas as pd
import pytest

import ego.mv_clustering.egon_data_io as db_io

from ego.mv_clustering import database


def pytest_configure(config):
    pytest.etrago_test_network_1_path = os.path.join(
        os.path.realpath(os.path.dirname(__file__)), "data/etrago_test_network_1"
    )
    pytest.interface_results_reference_data_path = os.path.join(
        os.path.realpath(os.path.dirname(__file__)),
        "data/interface_results_reference_data",
    )

    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def no_mv_lv_renewable_capacities(monkeypatch):
    """
    Replace the database queries of :class:`ETraGoMinimalData` for the wind and
    solar capacities in the medium and low voltage (MV/LV) grids by empty
    results, so that the eTraGo generators are kept unchanged and no database
    is needed.
    """
    monkeypatch.setattr(database, "get_engine", lambda: None)
    monkeypatch.setattr(database, "register_tables_in_saio", lambda engine: None)
    monkeypatch.setattr(db_io, "get_grid_ids", lambda **kwargs: pd.DataFrame())
    monkeypatch.setattr(
        db_io,
        "get_solar_capacity",
        lambda *args, **kwargs: pd.DataFrame({"solar_capacity_mw": []}, dtype=float),
    )
    monkeypatch.setattr(
        db_io,
        "get_wind_capacity",
        lambda *args, **kwargs: pd.DataFrame({"wind_capacity_mw": []}, dtype=float),
    )
