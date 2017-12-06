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
# import country selection
from tools.utilities import bus_by_country
import pandas as pd
from tools.io import geolocation_buses


"""
# import scenario settings **args of eTraGo
args = get_scenario_setting(json_file='scenario_setting.json')

# start eTraGo calculation
eTraGo = etrago(args['eTraGo'])

# add country code to bus and geometry (shapely)
# eTraGo.buses = eTraGo.buses.drop(['country_code','geometry'], axis=1)
##eTraGo.lines.info()

test = geolocation_buses(network = eTraGo, section='oedb')
"""
#test.buses

#plot_line_loading(eTraGo)


make_all_plots(eTraGo)


# write results to excel
#hv_generator_results(eTraGo)
"""


"""


if __name__ == '__main__':
    # import scenario settings **args of eTraGo
    args = get_scenario_setting(json_file='scenario_setting.json')



    # start eTraGo calculation
    eTraGo = etrago(args['eTraGo'])

    # add country code to bus and geometry (shapely)
    # eTraGo.buses = eTraGo.buses.drop(['country_code','geometry'], axis=1)
    ##eTraGo.lines.info()


    network =eTraGo
    test = geolocation_buses(network = eTraGo, section='oedb')



    # plots
    # make a line loading plot
    plot_line_loading(eTraGo)

    # plot stacked sum of nominal power for each generator type and timestep
    plot_stacked_gen(eTraGo, resolution="MW")

    # plot to show extendable storages
    storage_distribution(eTraGo)




    # start calculations (eTraGo and eDisGo)
    # rename resulting network container to eTraGo
    #eTraGo = etrago(args2)
    # eDisGo_network = edisgo()


    # test call plot function
    make_all_plots(eTraGo)



    # calculate power plant dispatch without grid utilization (either in pypsa or in renpassgis)

    # result queries...call functions from utilities

    ## total system costs of transmission grid vs. total system costs of all distribution grids results in overall total
    ## details on total system costs:
    ## existing plants: usage, costs for each technology
    ## newly installed plants (storages, grid measures) with size, location, usage, costs
    ## grid losses: amount and costs

    # possible aggregation of results

    # exports: total system costs, plots, csv export files
