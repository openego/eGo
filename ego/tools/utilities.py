"""
Utility functions of eGo
"""


import os
import pandas as pd
import json
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
    with open(path +'/'+json_file) as f:
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

    end   = args['eTraGo'].get('end_snapshot')
    start = args['eTraGo'].get('start_snapshot')
    time_step = end - start

    return time_step
