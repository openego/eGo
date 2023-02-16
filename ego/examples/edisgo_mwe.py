import os

from pypsa import Network as PyPSANetwork

from ego.tools.edisgo_integration import EDisGoNetworks
from ego.tools.utilities import get_scenario_setting

base_path = os.path.join(os.path.expanduser("~"), "git-repos", "data")

# eTraGo network is not yet disaggregated
etrago_network = PyPSANetwork(
    os.path.join(base_path, "etrago_results/disaggregated_network")
)
# manually overwrite bus ID to have busses in the chosen grid
# etrago_network.generators.loc[etrago_network.generators.bus == "16", "bus"] = "26533"

json_file = get_scenario_setting()

edisgo_networks = EDisGoNetworks(json_file=json_file, etrago_network=etrago_network)


etrago_network.generators.carrier.unique().tolist()
etrago_network.links.carrier.unique().tolist()
etrago_network.storage_units.carrier.unique().tolist()
etrago_network.stores.carrier.unique().tolist()
print("x")
