import os

from edisgo.tools.logger import setup_logger
from pypsa import Network as PyPSANetwork

from ego.mv_clustering.database import sshtunnel
from ego.tools.edisgo_integration import EDisGoNetworks
from ego.tools.utilities import get_scenario_setting

config = get_scenario_setting()

data_dir = config["eGo"]["data_dir"]
results_dir = config["eGo"]["results_dir"]

setup_logger(
    loggers=[
        {"name": "root", "file_level": "warning", "stream_level": "warning"},
        {"name": "ego", "file_level": "debug", "stream_level": "debug"},
        {"name": "edisgo", "file_level": None, "stream_level": None},
    ],
    file_name="ego.log",
    log_dir=results_dir,
)

base_path = os.path.join(os.path.expanduser("~"), "git-repos", "data", "ego")
data_dir = config["eGo"]["data_dir"]

etrago_network = PyPSANetwork(
    os.path.join(data_dir, "etrago_disaggregated_pf_post_lopf_false")
)

with sshtunnel(config=config):
    edisgo_networks = EDisGoNetworks(json_file=config, etrago_network=etrago_network)

print("THE END")
