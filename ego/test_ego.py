import sys
print ("Python version: " + sys.version + "\n")
print(sys.executable)
import pip
installed_packages = pip.get_installed_distributions()
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
     for i in installed_packages])
print(installed_packages_list)


import os # Operation system
print ("WD: " + os.getcwd() + "\n")

import pandas as pd
print ("Pandas Version: " + pd.__version__ + " (0.20.3 is for eDisGo, 0.19.1 for eTraGo)")

import logging # ToDo: Logger should be set up more specific
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import matplotlib.pyplot as plt

etrago = True
direct_specs = False
specs = True
edisgo = True


#%% Database Connection
from sqlalchemy.orm import sessionmaker
from egoio.tools import db
#from oemof import db
#conn = db.connection(section='oedb')

conn = db.connection(section='oedb')
Session = sessionmaker(bind=conn)
session = Session()


#%% eTraGo
if etrago:

    from tools.plots import make_all_plots

    from tools.utilities import get_scenario_setting
        # eTraGo
    from etrago.appl import etrago # This is the main function of etrago.
            # The import function
    #from etrago.tools.utilities import oedb_session


        # Import scenario settings **kwargs of eTraGo
    args = get_scenario_setting() # Gets scenario settings form json file.

    # session = oedb_session(args['eTraGo_args']['db']) # Same session class as used by eTraGo itself later, but diferent object
    # eDisGo uses the same session class.
    # Connection Parameters come from the Oemof config file


        # Start eTraGo calculation
    eTraGo = etrago(args['eTraGo']) # Baut über oemof.de (und config.ini eine Verbindung zur Datenbank auf)

        # Plot everything to console
    make_all_plots(eTraGo) # Line loading, commitment, storage


# Specs directily from etrago
if direct_specs:
    import pandas as pd
    bus_id = 27334



    specs_meta_data = {}
    specs_meta_data.update({'TG Bus ID':bus_id})

    # Retrieve all Data

    ### Snapshot Range
    #snap_idx = eTraGo_network.snapshots

    ## Bus Power
    try:
        active_power_kW = eTraGo_network.buses_t.p[str(bus_id)] * 1000 # PyPSA result is in MW
    except:
        logger.warning('No active power series')
        active_power_kW = None

    try:
        reactive_power_kvar = eTraGo_network.buses_t.q[str(bus_id)] * 1000 # PyPSA result is in Mvar
    except:
        logger.warning('No reactive power series')
        reactive_power_kvar = None


    ## Gens
    all_gens = eTraGo_network.generators.bus
    bus_gens = all_gens.index[all_gens == str(bus_id)]
    p_nom = eTraGo_network.generators.p_nom[bus_gens]
    gen_type = eTraGo_network.generators.carrier[bus_gens]

    gen_df = pd.DataFrame({'p_nom': p_nom,'gen_type':gen_type})
    capacity = gen_df[['p_nom','gen_type']].groupby('gen_type').sum().T

    gens = eTraGo_network.generators
    for key, value in gens.items():
        print (key)









#%% Specs
if specs:
    logging.info('Retrieving Specs')
#    subst_id = 1802
    bus_id = 23971
    result_id = 9
    scn_name = 'NEP 2035'# Six is Germany for 2 Snaps with minimal residual load

    from ego.tools.specs import get_etragospecs_from_db
    from egoio.db_tables import model_draft

    #ormclass_substation = model_draft.__getattribute__('EgoGridHvmvSubstation') # Even here, ther version should be checked

#    bus_id = 23971 # Two solars with identic w_id
## 23695 gas dispatch
#
## 26930
#result_id = 9

#    subst_id = session.query(
#            ormclass_substation.subst_id
#            ).filter(
#            ormclass_substation.otg_id == bus_id
#            ).scalar(
#                    )

    # ToDo: Here, a version check must be implemented (the data eTraGo uses e.g. 0.2.11 must mach the data ding0 used for its grids (e.g.0.3.0). Otherwise this match is not guaranteed)
#    bus_id = session.query(
#            ormclass_substation.otg_id
#            ).filter(
#            ormclass_substation.subst_id == subst_id
#            ).scalar(
#                    )

    specs = get_etragospecs_from_db(session, bus_id, result_id, scn_name)



#%% eDisGo
if edisgo:
    logging.info('Starting eDisGo')

    from datetime import datetime
    from edisgo.grid.network import Network, Scenario, TimeSeries, Results, ETraGoSpecs

    import networkx as nx

    file_path = '/home/dozeumbuw/ego_dev/src/ding0_grids__1802.pkl'
#    file_path = '/home/student/Git/eGo/ego/data/grids/test_grid.pkl'

    #mv_grid = open(file_path)

    mv_grid_id = file_path.split('_')[-1].split('.')[0]

    power_flow = (datetime(2011, 5, 26, 12), datetime(2011, 5, 26, 13)) # Where retrieve from? Database or specs?


    timeindex = pd.date_range(power_flow[0], power_flow[1], freq='H')

    scenario = Scenario(etrago_specs=specs,
                        power_flow=(),
                        mv_grid_id=mv_grid_id,
                        scenario_name='NEP 2035')

    network = Network.import_from_ding0(file_path,
                                        id=mv_grid_id,
                                        scenario=scenario)
    network.analyze()


    nx.draw(network.mv_grid.graph)
    plt.draw()
    plt.show()



    network.results.v_res(#nodes=network.mv_grid.graph.nodes(),
            level='mv')
    network.results.s_res()

    # A status quo grid (without new renewable gens) should not need reinforcement
#    network.reinforce()

    # Do grid reinforcement
    network.reinforce()

#    network.results = Results()
    costs = network.results.grid_expansion_costs
    print(costs)
