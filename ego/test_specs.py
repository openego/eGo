################################################################################
# Example I

from edisgo.grid.network import Network, Scenario


file_path = '/home/dozeumbuw/ego_dev/src/ding0_grids__1802.pkl'
mv_grid_id = file_path.split('_')[-1].split('.')[0]

# Define a scenario
scenario = Scenario(power_flow='worst-case', mv_grid_id=mv_grid_id)

# Get the grid topology data
network = Network.import_from_ding0(
    file_path,
    id=mv_grid_id,
    scenario=scenario)

# Import future generators
network.import_generators(types=['wind', 'solar']) # Import error Att.: preversion -> ego.io version / branch?

# Do non-linear power flow analysis with PyPSA
network.analyze()

# Do grid reinforcement
network.reinforce()

# Determine cost for each line/transformer that was reinforced
costs = network.results.grid_expansion_costs

costs
################################################################################
# Example II

import pandas as pd
from datetime import date
from edisgo.grid.network import Network, Scenario, ETraGoSpecs

file_path = '/home/dozeumbuw/ego_dev/src/ding0_grids__1802.pkl'
mv_grid_id = file_path.split('_')[-1].split('.')[0]


# Define eTraGo specs
timeindex = pd.date_range(date(2017, 10, 10), date(2017, 10, 13),
                          freq='H')
etrago_specs = ETraGoSpecs(
    conv_dispatch=pd.DataFrame({'biomass': [1] * len(timeindex),
                                'coal': [1] * len(timeindex),
                                'gas': [1] * len(timeindex)},
                               index=timeindex),
    ren_dispatch=pd.DataFrame({'0': [0.2] * len(timeindex),
                               '1': [0.3] * len(timeindex),
                               '2': [0.4] * len(timeindex),
                               '3': [0.5] * len(timeindex)},
                              index=timeindex),
    curtailment=pd.DataFrame({'0': [0.0] * len(timeindex),
                              '1': [0.0] * len(timeindex),
                              '2': [0.1] * len(timeindex),
                              '3': [0.1] * len(timeindex)},
                             index=timeindex),
    renewables=pd.DataFrame({
        'name': ['wind', 'wind', 'solar', 'solar'],
        'w_id': ['1', '2', '1', '2'],
        'ren_id': ['0', '1', '2', '3']}, index=[0, 1, 2, 3]),
    battery_capacity=100,
    battery_active_power=pd.Series(data=[50, 20, -10, 20])
    )

# Define a scenario
scenario = Scenario(power_flow=(), mv_grid_id=mv_grid_id,
                    etrago_specs=etrago_specs)

# Get the grid topology data
network = Network.import_from_ding0(
    file_path,
    id=mv_grid_id,
    scenario=scenario)

# Import future generators
network.import_generators(types=['wind', 'solar'])

# Do non-linear power flow analysis with PyPSA
network.analyze()

# Do grid reinforcement
network.reinforce()

# Determine cost for each line/transformer that was reinforced
costs = network.results.grid_expansion_costs
costs
