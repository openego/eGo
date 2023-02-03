import os

from pypsa import Network as PyPSANetwork

from ego.tools.edisgo_integration import EDisGoNetworks
from ego.tools.utilities import get_scenario_setting

base_path = "/home/birgit/virtualenvs/eGo_interface_development/git_repos"

# eTraGo network is not yet disaggregated
etrago_network = PyPSANetwork(os.path.join(base_path, "data/eTraGo_results"))
# manually overwrite bus ID to have busses in the chosen grid
etrago_network.generators.loc[etrago_network.generators.bus == "16", "bus"] = "26533"

json_file = get_scenario_setting()

edisgo_networks = EDisGoNetworks(json_file=json_file, etrago_network=etrago_network)

print("x")
