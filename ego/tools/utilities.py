import json
import os

# import scenario settings **args

def get_scenario_setting(json_file='scenario_setting.json'):
    """ Get and open json file with scenaio settings of eGo

    Parameter:
    ----------

    json_file (str):
        default: 'scenario_setting.json'
        Name of scenario setting json file
    """
    path = os.getcwd()
    with open(path +'/'+json_file) as f:
      scn_set = json.load(f)

    if scn_set['global'].get('eTraGo') == True:
        print('Use eTraGo settings')

    if scn_set['global'].get('eDisGo') == True:
        print('Use eDisGo settings')

    return scn_set


def get_etrago_scnario():





    return scenario_setting
