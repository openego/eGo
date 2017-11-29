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

def get_time_steps(args):
    """ Get time step of calculation by scenario settings.

    Parameter:
    ----------
    args (dict):
        dict of 'scenario_setting.json'

    Result:
    -------
    time_step (int):
        Number of timesteps of the calculation.
    """

    end   = args['eTraGo'].get('end_snapshot')
    start = args['eTraGo'].get('start_snapshot')
    time_step = end - start

    return time_step


def bus_by_country(network):
    """
    part taken from etrago.tools.utilities.clip_foreign

    

    """
     # get foreign buses by country
    poland = pd.Series(index=network.buses[(network.buses['x'] > 17)].index,
                                                  data="Poland")
    czech = pd.Series(index=network.buses[(network.buses['x'] < 17) &
                                            (network.buses['x'] > 15.1)].index,
                                            data="Czech")
    denmark = pd.Series(index=network.buses[((network.buses['y'] < 60) &
                                            (network.buses['y'] > 55.2)) |
                                            ((network.buses['x'] > 11.95) &
                                               (network.buses['x'] < 11.97) &
                                               (network.buses['y'] > 54.5))].index,
                                            data="Denmark")
    sweden = pd.Series(index=network.buses[(network.buses['y'] > 60)].index,
                                            data="Sweden")
    austria = pd.Series(index=network.buses[(network.buses['y'] < 47.33) &
                                            (network.buses['x'] > 9) |
                                            ((network.buses['x'] > 9.65) &
                                            (network.buses['x'] < 9.9) &
                                            (network.buses['y'] < 47.5) &
                                            (network.buses['y'] > 47.3)) |
                                            ((network.buses['x'] > 12.14) &
                                            (network.buses['x'] < 12.15) &
                                            (network.buses['y'] > 47.57) &
                                            (network.buses['y'] < 47.58)) |
                                            (network.buses['y'] < 47.6) &
                                            (network.buses['x'] > 14.1)].index,
                                            data="Austria")
    switzerland = pd.Series(index=network.buses[((network.buses['x'] > 8.1) &
                                                 (network.buses['x'] < 8.3) &
                                                 (network.buses['y'] < 46.8)) |
                                                 ((network.buses['x'] > 7.82) &
                                                 (network.buses['x'] < 7.88) &
                                                 (network.buses['y'] > 47.54) &
                                                 (network.buses['y'] < 47.57)) |
                                                 ((network.buses['x'] > 10.91) &
                                                 (network.buses['x'] < 10.92) &
                                                 (network.buses['y'] > 49.91) &
                                                 (network.buses['y'] < 49.92))].index,
                                                data="Switzerland")
    netherlands = pd.Series(index=network.buses[((network.buses['x'] < 6.96) &
                                               (network.buses['y'] < 53.15) &
                                               (network.buses['y'] > 53.1)) |
                                                ((network.buses['x'] < 5.4) &
                                               (network.buses['y'] > 52.1))].index,
                                                data = "Netherlands")
    luxembourg = pd.Series(index=network.buses[((network.buses['x'] < 6.15) &
                                               (network.buses['y'] < 49.91) &
                                               (network.buses['y'] > 49.65))].index,
                                                data="Luxembourg")
    france = pd.Series(index=network.buses[(network.buses['x'] < 4.5) |
                                            ((network.buses['x'] > 7.507) &
                                            (network.buses['x'] < 7.508) &
                                            (network.buses['y'] > 47.64) &
                                            (network.buses['y'] < 47.65)) |
                                            ((network.buses['x'] > 6.2) &
                                            (network.buses['x'] < 6.3) &
                                            (network.buses['y'] > 49.1) &
                                            (network.buses['y'] < 49.2)) |
                                            ((network.buses['x'] > 6.7) &
                                            (network.buses['x'] < 6.76) &
                                            (network.buses['y'] > 49.13) &
                                            (network.buses['y'] < 49.16))].index,
                                            data="France")
    foreign_buses = pd.Series()
    foreign_buses = foreign_buses.append([poland, czech, denmark, sweden, austria, switzerland,
                          netherlands, luxembourg, france])

    return foreign_buses
