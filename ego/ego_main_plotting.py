"""
Plot testing
"""

import pandas as pd
import os

if not 'READTHEDOCS' in os.environ:
    from etrago.appl import etrago

    # For importing geopandas you need to install spatialindex on your system http://github.com/libspatialindex/libspatialindex/wiki/1.-Getting-Started
    from tools.utilities import get_scenario_setting, get_time_steps
    from tools.io import geolocation_buses, etrago_from_oedb
    from tools.results import total_storage_charges, eGoResults
    from sqlalchemy.orm import sessionmaker
    from egoio.tools import db
    from etrago.tools.io import results_to_oedb
    from tools.plots import (make_all_plots,plot_line_loading, plot_stacked_gen,
                                     add_coordinates, curtailment, gen_dist,
                                     storage_distribution, igeoplot,
                                     plotting_invest, plot_storage_use,
                                     total_power_costs_plot,
                                     plot_etrago_production)

# ToDo: Logger should be set up more specific
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# import scenario settings **args of eTraGo
args = get_scenario_setting(json_file='scenario_setting.json')

try:
    conn = db.connection(section=args['global']['db'])
    Session = sessionmaker(bind=conn)
    session = Session()
except OperationalError:
    logger.error('Failed connection to Database',  exc_info=True)

# start calculations of eTraGo if true

# start eTraGo calculation
eTraGo = etrago(args['eTraGo'])


r = eGoResults(eTraGo=eTraGo, eDisGo=None)
ego = r.create_total_results()

ego.investment
ego.etrago
ego.storages


###############################################################
#get all plots

plotting_invest(ego)
plot_storage_use(ego.storages)
total_power_costs_plot(eTraGo)



make_all_plots(eTraGo)


#ego.etrago
#ego.storages


eTraGo.pf


#igeoplot(eTraGo, session, tiles=None, geoloc=None, args=None)
plot_etrago_production(eTraGo)
total_power_costs_plot(eTraGo)
