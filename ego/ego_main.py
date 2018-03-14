"""
This is the application file for the tool eGo. The application eGo calculates
the distribution and transmission grids of eTraGo and eDisGo.

.. warning::
    Note, that this Repository is under construction and relies on data provided
    by the OEDB. Currently, only members of the openego project team have access
    to this database.

"""
__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität"\
                            "Flensburg, Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolfbunke, maltesc"

import pandas as pd
import os

if not 'READTHEDOCS' in os.environ:
    from etrago.appl import etrago
    from tools.plots import (make_all_plots,plot_line_loading, plot_stacked_gen,
                                     add_coordinates, curtailment, gen_dist,
                                     storage_distribution, igeoplot)
    # For importing geopandas you need to install spatialindex on your system http://github.com/libspatialindex/libspatialindex/wiki/1.-Getting-Started
    from tools.utilities import get_scenario_setting, get_time_steps
    from tools.io import geolocation_buses, etrago_from_oedb
    from tools.results import total_storage_charges
    from sqlalchemy.orm import sessionmaker
    from egoio.tools import db
    from etrago.tools.io import results_to_oedb

# ToDo: Logger should be set up more specific
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    # import scenario settings **args of eTraGo
    args = get_scenario_setting(json_file='scenario_setting.json')
    print (args)

    try:
        conn = db.connection(section=args['global']['db'])
        Session = sessionmaker(bind=conn)
        session = Session()
    except OperationalError:
        logger.error('Failed connection to Database',  exc_info=True)

    # start calculations of eTraGo if true
    if args['global']['eTraGo']:
        # start eTraGo calculation
        eTraGo = etrago(args['eTraGo'])

        
        # add country code to bus and geometry (shapely)
        # eTraGo.buses = eTraGo.buses.drop(['country_code','geometry'], axis=1)
        #test = geolocation_buses(network = eTraGo, session)

        # other plots based on matplotlib
        make_all_plots(eTraGo)
        # make a line loading plot
        plot_line_loading(eTraGo)

        # plot stacked sum of nominal power for each generator type and timestep
        plot_stacked_gen(eTraGo, resolution="MW")

        # plot to show extendable storages
        storage_distribution(eTraGo)

        # plot storage total charges and discharge
        total_storage_charges(eTraGo, plot=True)

    # get eTraGo results form db
    if args['global']['recover']:
        eTraGo = etrago_from_oedb(session,args)



    # use eTraGo results from ego calculations if true
    # ToDo make function edisgo_direct_specs()



    if args['eDisGo']['direct_specs']:
        # ToDo: add this to utilities.py

        logging.info('Retrieving Specs')

        bus_id = 27574 #23971

        from ego.tools.specs import get_etragospecs_direct, get_mvgrid_from_bus_id
        from egoio.db_tables import model_draft
        specs = get_etragospecs_direct(session, bus_id, eTraGo, args)



    # ToDo make loop for all bus ids
    #      make function which links bus_id (subst_id)
    if args['eDisGo']['specs']:


        logging.info('Retrieving Specs')
        # ToDo make it more generic
        # ToDo iteration of grids
        # ToDo move part as function to utilities or specs
        bus_id = 27574 #23971
        result_id = args['global']['result_id']

        from ego.tools.specs import get_etragospecs_from_db, get_mvgrid_from_bus_id
        from egoio.db_tables import model_draft
        specs = get_etragospecs_from_db(session, bus_id, result_id)

        mv_grid = get_mvgrid_from_bus_id(session, bus_id) # This function can be used to call the correct MV grid

    if args['global']['eDisGo']:
        logging.info('Starting eDisGo')

        # ToDo move part as function to utilities or specs
        from datetime import datetime
        from edisgo.grid.network import Network, Scenario, TimeSeries, Results, ETraGoSpecs
        import networkx as nx
        import matplotlib.pyplot as plt

        # ToDo get ding0 grids over db
        # ToDo implemente iteration
        file_path = '/home/dozeumbuw/ego_dev/src/ding0_grids__1802.pkl'

        #mv_grid = open(file_path)

        mv_grid_id = file_path.split('_')[-1].split('.')[0]
        power_flow = (datetime(2011, 5, 26, 12), datetime(2011, 5, 26, 13)) # Where retrieve from? Database or specs?

        timeindex = pd.date_range(power_flow[0], power_flow[1], freq='H')

        scenario = Scenario(etrago_specs=specs,
                    power_flow=(),
                    mv_grid_id=mv_grid_id,
                    scenario_name= args['global']['scn_name'])

        network = Network.import_from_ding0(file_path,
                                    id=mv_grid_id,
                                    scenario=scenario)
        # check SQ MV grid
        network.analyze()

        network.results.v_res(#nodes=network.mv_grid.graph.nodes(),
                level='mv')
        network.results.s_res()

        # A status quo grid (without new renewable gens) should not need reinforcement
        network.reinforce()


        nx.draw(network.mv_grid.graph)
        plt.draw()
        plt.show()

        #    network.results = Results()
        costs = network.results.grid_expansion_costs
        print(costs)


    # make interactive plot with folium
    #logging.info('Starting interactive plot')
    #igeoplot(network=eTraGo, session=session, args=args)    # ToDo: add eDisGo results

    # calculate power plant dispatch without grid utilization (either in pypsa or in renpassgis)

    # result queries...call functions from utilities

    ## total system costs of transmission grid vs. total system costs of all distribution grids results in overall total
    ## details on total system costs:
    ## existing plants: usage, costs for each technology
    ## newly installed plants (storages, grid measures) with size, location, usage, costs
    ## grid losses: amount and costs

    # possible aggregation of results

    # exports: total system costs, plots, csv export files
