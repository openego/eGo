"""
This is the application file for the tool eGo. The application eGo calculates the distribution and transmission grids
of eTraGo and eDisGo.


Warrning: This Repository is underconstruction and work in progress (wip)

"""
__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität Flensburg, Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolfbunke"

from etrago.appl import etrago
from tools.plots import (make_all_plots,plot_line_loading, plot_stacked_gen,
                                     add_coordinates, curtailment, gen_dist,
                                     storage_distribution, igeoplot)
from tools.utilities import get_scenario_setting, get_time_steps, bus_by_country
#from eDisGo import ...
# use spects
# import country selection
import pandas as pd
from tools.io import geolocation_buses
from egoio.tools import db
from sqlalchemy.orm import sessionmaker
import logging
logger = logging.getLogger(__name__)



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

# write results to excel
#hv_generator_results(eTraGo)



if __name__ == '__main__':
    # import scenario settings **args of eTraGo
    args = get_scenario_setting(json_file='scenario_setting.json')


    # start eTraGo calculation
    eTraGo = etrago(args['eTraGo'])

    # add country code to bus and geometry (shapely)
    # eTraGo.buses = eTraGo.buses.drop(['country_code','geometry'], axis=1)
    ##eTraGo.lines.info()
    try:
        conn = db.connection(section=args['eTraGo']['db'])
        Session = sessionmaker(bind=conn)
        session = Session()
    except OperationalError:
        logger.error('Failed connection to Database',  exc_info=True)

    igeoplot(eTraGo, session)

    #network =eTraGo
    #test = geolocation_buses(network = eTraGo, session)

    #igeoplot(network =eTraGo)

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
    #make_all_plots(eTraGo)



    # calculate power plant dispatch without grid utilization (either in pypsa or in renpassgis)

    # result queries...call functions from utilities

    ## total system costs of transmission grid vs. total system costs of all distribution grids results in overall total
    ## details on total system costs:
    ## existing plants: usage, costs for each technology
    ## newly installed plants (storages, grid measures) with size, location, usage, costs
    ## grid losses: amount and costs

    # possible aggregation of results

    # exports: total system costs, plots, csv export files
