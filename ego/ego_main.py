"""
This is the application file for the tool eGo. The application eGo calculates
the distribution and transmission grids of eTraGo and eDisGo.

.. warning::
    Note, that this Repository is under construction and relies on data provided
    by the OEDB. Currently, only members of the openego project team have access
    to this database.

"""
__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc"

import pandas as pd
import os

from ego.tools.utilities import define_logging
logger = define_logging(log_name='ego.log')

from ego.tools.io import eGo

# if not 'READTHEDOCS' in os.environ:
#    from tools.io import eGo
#from etrago.tools.io import results_to_oedb


if __name__ == '__main__':

        # import scenario settings **args of eTraGo
    logger.info('Start calculation')

    ego = eGo(jsonpath='scenario_setting.json')
    ego.etrago_line_loading()


"""

    # add country code to bus and geometry (shapely)
    # eTraGo.buses = eTraGo.buses.drop(['country_code','geometry'], axis=1)
    # test = geolocation_buses(network = eTraGo, session)

    # get eTraGo results form db
    if args['global']['recover']:
     # TODO add it to class
        eTraGo = etrago_from_oedb(session, args)

    # use eTraGo results from ego calculations if true
    # ToDo make function edisgo_direct_specs()

    if args['eDisGo']['direct_specs']:
        # ToDo: add this to utilities.py

        logger.info('Retrieving Specs')

        bus_id = 25402  # 23971

        from ego.tools.specs import get_etragospecs_direct, get_mvgrid_from_bus_id
        from egoio.db_tables import model_draft
        specs = get_etragospecs_direct(session, bus_id, eTraGo, args)

    # ToDo make loop for all bus ids
    #      make function which links bus_id (subst_id)
    if args['eDisGo']['specs']:

        logger.info('Retrieving Specs')
        # ToDo make it more generic
        # ToDo iteration of grids
        # ToDo move part as function to utilities or specs
        bus_id = 25402  # 27574  # 23971
        result_id = args['global']['result_id']

        from ego.tools.specs import get_etragospecs_from_db, get_mvgrid_from_bus_id
        from egoio.db_tables import model_draft
        specs = get_etragospecs_from_db(session, bus_id, result_id)

        # This function can be used to call the correct MV grid
        mv_grid = get_mvgrid_from_bus_id(session, bus_id)

    if args['global']['eDisGo']:

        logger.info('Starting eDisGo')

        # ToDo move part as function to utilities or specs
        from datetime import datetime
        from edisgo.grid.network import (Network, Scenario,
                                         TimeSeries, Results, ETraGoSpecs)
        import networkx as nx
        import matplotlib.pyplot as plt

        # ToDo get ding0 grids over db
        # ToDo implemente iteration
        file_path = 'data/ding0_grids/ding0_grids__1802.pkl'

        #mv_grid = open(file_path)

        mv_grid_id = file_path.split('_')[-1].split('.')[0]
        # Where retrieve from? Database or specs?
        power_flow = (datetime(2011, 5, 26, 12), datetime(2011, 5, 26, 13))

        timeindex = pd.date_range(power_flow[0], power_flow[1], freq='H')

        scenario = Scenario(etrago_specs=specs,
                            power_flow=(),
                            mv_grid_id=mv_grid_id,
                            scenario_name=args['eTraGo']['scn_name'])

        network = Network.import_from_ding0(file_path,
                                            id=mv_grid_id,
                                            scenario=scenario)
        # check SQ MV grid
        network.analyze()

        network.results.v_res(  # nodes=network.mv_grid.graph.nodes(),
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
    #logger.info('Starting interactive plot')
    # igeoplot(network=eTraGo, session=session, args=args)    # ToDo: add eDisGo results

    # calculate power plant dispatch without grid utilization (either in pypsa or in renpassgis)

    # result queries...call functions from utilities

    # total system costs of transmission grid vs. total system costs of all distribution grids results in overall total
    # details on total system costs:
    # existing plants: usage, costs for each technology
    # newly installed plants (storages, grid measures) with size, location, usage, costs
    # grid losses: amount and costs

    # possible aggregation of results

    # exports: total system costs, plots, csv export files

"""
"""
# Using graphviz for Calculation Dokumentation.

from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput

def main():
    graphviz = GraphvizOutput()
    graphviz.output_file = 'basic.png'

    with PyCallGraph(output=graphviz):
        logger.info('Start calculation')

        ego = eGo(jsonpath='scenario_setting.json')

        print(ego.etrago.storage_charges)
        ego.etrago_network.plot()

if __name__ == '__main__':
    main()
"""
