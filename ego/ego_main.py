"""
Main script of eGo.


Work in progress (wip)

"""
__copyright__ = "tba"
__license__ = "tba"
__author__ = "tba"

from etrago.appl import etrago
from tools.plots import (make_all_plots,plot_line_loading, plot_stacked_gen,
                                     add_coordinates, curtailment, gen_dist,
                                     storage_distribution)
from tools.utilities import get_scenario_setting
#from eDisGo import ...


# import scenario settings **args of eTraGo
args = get_scenario_setting()

# start eTraGo calculation
eTraGo_network = etrago(args)

make_all_plots(eTraGo_network)


# get time of calculation
calc_time = args['end_snapshot'] - args['start_snapshot']
print(calc_time)

p_nom_o_sum = eTraGo_network.generators.p_nom_opt.sum()  # in [MWh]
p_nom_sum = eTraGo_network.generators.p_nom.sum()  # in [MWh]
m_cost_sum = eTraGo_network.generators.marginal_cost.sum() # in [EUR]

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
