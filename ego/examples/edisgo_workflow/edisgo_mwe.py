import os

from pypsa import Network as PyPSANetwork

from ego.tools.edisgo_integration import EDisGoNetworks
from ego.tools.utilities import get_scenario_setting

config = get_scenario_setting()
data_dir = config["eGo"]["data_dir"]

etrago_network = PyPSANetwork(
    os.path.join(data_dir, "etrago_disaggregated_pf_post_lopf_false")
)

edisgo_networks = EDisGoNetworks(json_file=config, etrago_network=etrago_network)

print("THE END")
