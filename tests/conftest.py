import os

import pytest


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
