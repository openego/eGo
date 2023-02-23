# flake8: noqa: E402
import warnings

warnings.filterwarnings("ignore")

import os

from edisgo.tools.logger import setup_logger
from pypsa import Network as PyPSANetwork

from ego.tools.edisgo_integration import EDisGoNetworks
from ego.tools.utilities import get_scenario_setting

setup_logger(
    loggers=[
        {"name": "root", "file_level": None, "stream_level": "warning"},
        {"name": "ego", "file_level": None, "stream_level": "debug"},
        {"name": "edisgo", "file_level": None, "stream_level": "info"},
    ]
)

base_path = os.path.join(os.path.expanduser("~"), "git-repos", "data", "ego")
config = get_scenario_setting(jsonpath="cluster_setting.json")

pf_post_lopf = config["eTraGo"]["pf_post_lopf"]

if pf_post_lopf:
    file_name = "etrago_disaggregated_pf_post_lopf_true"
else:
    file_name = "etrago_disaggregated_pf_post_lopf_false"

etrago_network = PyPSANetwork(os.path.join(base_path, file_name))
edisgo_networks = EDisGoNetworks(json_file=config, etrago_network=etrago_network)

print("THE END")
