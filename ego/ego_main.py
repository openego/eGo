"""
This is the application file for the tool eGo. The application eGo calculates the distribution and transmission grids
of eTraGo and eDisGo.

Warrning: This Repository is underconstruction and work in progress (wip)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität Flensburg, Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolfbunke"


from etrago.appl import etrago
from tools.plots import (make_all_plots,plot_line_loading, plot_stacked_gen,
                                     add_coordinates, curtailment, gen_dist,
                                     storage_distribution)
from tools.utilities import get_scenario_setting, get_time_steps
#from eDisGo import ...

# import scenario settings **args of eTraGo
args = get_scenario_setting()

# start eTraGo calculation
eTraGo_network = etrago(args['eTraGo'])



def hv_generator_results(eTraGo_network):

    eTraGo_network.generators.groupby('carrier')['p_nom'].sum() # in MW

    eTraGo_network.generators.groupby('carrier')['p_nom_opt'].sum() # in MW

    eTraGo_network.generators.groupby('carrier')['marginal_cost'].sum() # in in [EUR]

    calc_time = get_time_steps(args)

    p_nom_o_sum = eTraGo_network.generators.p_nom_opt.sum()  # in [MWh]
    p_nom_sum = eTraGo_network.generators.p_nom.sum()  # in [MWh]
    m_cost_sum = eTraGo_network.generators.marginal_cost.sum() # in [EUR]

    return




eTraGo_network.generators.p_nom_opt.sum()


eTraGo_network

make_all_plots(eTraGo_network)


# cost per €/MWh
price = m_cost_sum/p_nom__o_sum
print(price)

p_nom_o_sum - p_nom_sum



eTraGo_network.generators.head()


# plots
# make a line loading plot
plot_line_loading(eTraGo_network)

# plot stacked sum of nominal power for each generator type and timestep
plot_stacked_gen(network, resolution="MW")

# plot to show extendable storages
storage_distribution(network)




# start calculations (eTraGo and eDisGo)
# rename resulting network container to eTraGo_network
#eTraGo_network = etrago(args2)
# eDisGo_network = edisgo()


# test call plot function
make_all_plots(eTraGo_network)



# calculate power plant dispatch without grid utilization (either in pypsa or in renpassgis)

# result queries...call functions from utilities

## total system costs of transmission grid vs. total system costs of all distribution grids results in overall total
## details on total system costs:
## existing plants: usage, costs for each technology
## newly installed plants (storages, grid measures) with size, location, usage, costs
## grid losses: amount and costs

# possible aggregation of results

# exports: total system costs, plots, csv export files
