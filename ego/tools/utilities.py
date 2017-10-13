import json
import os

# import scenario settings **args

def get_scenario_setting():
    path = os.getcwd()
    with open(path +'/scenario_setting.json') as f:
      scenario_setting = json.load(f)

    return scenario_setting
