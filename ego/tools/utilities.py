"""
Utility functions of eGo

"""
import os
import pandas as pd
import json
import logging

__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke"


def define_logging(log_name='ego.log'):
    """Helpers to log your modeling process with eGo and defines all settings.


    """
    # ToDo: Logger should be set up more specific
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Logging
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logger = logging.getLogger(__name__)
    ego_logger = logging.getLogger('ego')

    fh = logging.FileHandler(log_name, mode='w')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - \
                                   %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    ego_logger.addHandler(fh)

    return ego_logger


# import scenario settings **args
def get_scenario_setting(json_file='scenario_setting.json'):
    """ Get and open json file with scenaio settings of eGo

    Parameters
    ----------

    json_file (str):
        default: 'scenario_setting.json'
        Name of scenario setting json file
    """
    path = os.getcwd()
    # add try ego/
    print(path)
    with open(path + '/'+json_file) as f:
        scn_set = json.load(f)

    if scn_set['global'].get('eTraGo') == True:
        print('Use eTraGo settings')
        sh_scen = ["SH Status Quo", "SH NEP 2035", "SH eGo 100"]
        if scn_set['eTraGo'].get('scn_name') in sh_scen and scn_set['eTraGo'].\
                get('gridversion') == "v0.3.0":
            scn_set['eTraGo']['gridversion'] = None

    if scn_set['global'].get('eDisGo') == True:
        print('Use eDisGo settings')

    return scn_set


def get_time_steps(args):
    """ Get time step of calculation by scenario settings.

    Parameters
    ----------
    args (dict):
        dict of 'scenario_setting.json'

    Returns
    -------
    time_step (int):
        Number of timesteps of the calculation.
    """

    end = args['eTraGo'].get('end_snapshot')
    start = args['eTraGo'].get('start_snapshot')
    time_step = end - start

    return time_step
