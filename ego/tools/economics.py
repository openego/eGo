# -*- coding: utf-8 -*-
# Copyright 2016-2018 Europa-Universität Flensburg,
# Flensburg University of Applied Sciences,
# Centre for Sustainable Energy Systems
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# File description
"""This module collects useful functions for economic calculation of eGo
which can mainly distinguished in operational and investment costs.
"""

import io
import pkgutil
import os
import logging
logger = logging.getLogger('ego')

if not 'READTHEDOCS' in os.environ:
    import pandas as pd
    import numpy as np
    from ego.tools.utilities import get_time_steps
    from etrago.tools.utilities import geolocation_buses

__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität"\
    "Flensburg, Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolfbunke"


# calculate annuity per time step or periode
def annuity_per_period(capex, n, wacc, t, p):
    """ Calculate per given period

    Parameters
    ----------
    capex : float
        Capital expenditure (NPV of investment)
    n : int
        Number of years that the investment is used (economic lifetime)
    wacc : float
        Weighted average cost of capital
    t : int
        Timesteps in hours
    p : float
        interest rate

    """

    # ToDo change formular to hourly annuity costs
    return capex * (wacc * (1 + wacc) ** n) / ((1 + wacc) ** n - 1)


def edisgo_convert_capital_costs(overnight_cost, t, p, json_file):
    """ Get scenario and calculation specific annuity cost by given capital
    costs and lifetime.


    Parameters
    ----------
    json_file : :obj:dict
        Dictionary of the ``scenario_setting.json`` file
    _start_snapshot : int
        Start point of calculation from ``scenario_setting.json`` file
    _end_snapshot : int
        End point of calculation from ``scenario_setting.json`` file
    _p : numeric
        interest rate of investment
    _t : int
        lifetime of investment

    Returns
    -------
    annuity_cost : numeric
        Scenario and calculation specific annuity cost by given capital
        costs and lifetime

    Examples
    --------
    .. math::

        PVA =   (1 / p) - (1 / (p*(1 + p)^t))

    """
    # Based on eTraGo calculation in
    # https://github.com/openego/eTraGo/blob/dev/etrago/tools/utilities.py#L651

    # Calculate present value of an annuity (PVA)
    PVA = (1 / p) - (1 / (p*(1 + p) ** t))

    year = 8760
    # get period of calculation
    period = (json_file['eTraGo']['end_snapshot']
              - json_file['eTraGo']['start_snapshot'])

    # calculation of capital_cost
    annuity_cost = (overnight_cost / (PVA * (year/(period+1))))

    return annuity_cost


def etrago_convert_overnight_cost(annuity_cost, json_file, t=40, p=0.05):
    """ Get annuity cost of simulation and calculation total
    ``overnight_costs`` by given capital costs and lifetime.

    Parameters
    ----------
    json_file : :obj:dict
        Dictionary of the ``scenario_setting.json`` file
    _start_snapshot : int
        Start point of calculation from ``scenario_setting.json`` file
    _end_snapshot : int
        End point of calculation from ``scenario_setting.json`` file
    _p : numeric
        interest rate of investment
    _T : int
        lifetime of investment

    Returns
    -------
    overnight_cost : numeric
        Scenario and calculation total ``overnight_costs`` by given
        annuity capital costs and lifetime.

    Examples
    --------
    .. math::

        PVA =   (1 / p) - (1 / (p*(1 + p)^t))

        K_{ON} = K_a*PVA*((t/(period+1))

    """
    # Based on eTraGo calculation in
    # https://github.com/openego/eTraGo/blob/dev/etrago/tools/utilities.py#L651

    # Calculate present value of an annuity (PVA)
    PVA = (1 / p) - (1 / (p*(1 + p) ** t))

    year = 8760
    # get period of calculation
    period = (json_file['eTraGo']['end_snapshot']
              - json_file['eTraGo']['start_snapshot'])

    # calculation of overnight_cost
    overnight_cost = annuity_cost*(PVA * (year/(period+1)))

    return overnight_cost


def etrago_operating_costs(network):
    """ Function to get all operating costs of eTraGo.

    Parameters
    ----------
    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`

    Returns
    -------
    operating_costs :  :pandas:`pandas.Dataframe<dataframe>`
        DataFrame with aggregate operational costs per component and voltage
        level in [EUR] per calculated time steps.

    Example
    -------

    .. code-block:: python

       >>> from ego.tools.io import eGo
       >>> ego = eGo(jsonpath='scenario_setting.json')
       >>> ego.etrago.operating_costs

    +-------------+-------------------+------------------+
    | component   |operation_costs    |  voltage_level   |
    +=============+===================+==================+
    |biomass      |   27.0            |      ehv         |
    +-------------+-------------------+------------------+
    |line losses  |    0.0            |      ehv         |
    +-------------+-------------------+------------------+
    |wind_onshore |    0.0            |      ehv         |
    +-------------+-------------------+------------------+

    """

    etg = network

    # get v_nom
    _bus = pd.DataFrame(etg.buses['v_nom'])
    _bus.index.name = "name"
    _bus.reset_index(level=0, inplace=True)

    # Add voltage level
    idx = etg.generators.index
    etg.generators = pd.merge(etg.generators, _bus,
                              left_on='bus', right_on='name')
    etg.generators.index = idx

    etg.generators['voltage_level'] = 'unknown'

    # add ehv
    ix_ehv = etg.generators[etg.generators['v_nom'] >= 380].index
    etg.generators.set_value(ix_ehv, 'voltage_level', 'ehv')
    # add hv
    ix_hv = etg.generators[(etg.generators['v_nom'] <= 220) &
                           (etg.generators['v_nom'] >= 110)].index
    etg.generators.set_value(ix_hv, 'voltage_level', 'hv')

    # get voltage_level index
    ix_by_ehv = etg.generators[etg.generators.voltage_level == 'ehv'].index
    ix_by_hv = etg.generators[etg.generators.voltage_level == 'hv'].index
    ix_slack = etg.generators[etg.generators.control != 'Slack'].index

    ix_by_ehv = ix_slack.join(ix_by_ehv, how='left', level=None,
                              return_indexers=False, sort=False)
    ix_by_hv = ix_slack.join(ix_by_hv, how='right', level=None,
                             return_indexers=False, sort=False)

    # groupby v_nom ehv
    operating_costs_ehv = (etg.generators_t.p[ix_by_ehv] *
                           etg.generators. marginal_cost[ix_by_ehv])
    operating_costs_ehv = operating_costs_ehv.groupby(
        etg.generators.carrier, axis=1).sum().sum()

    operating_costs = pd.DataFrame(operating_costs_ehv)
    operating_costs.columns = ['operation_costs']
    operating_costs['voltage_level'] = 'ehv'
    # groupby v_nom ehv
    operating_costs_hv = (etg.generators_t.p[ix_by_hv] *
                          etg.generators. marginal_cost[ix_by_hv])
    operating_costs_hv = operating_costs_hv.groupby(
        etg.generators.carrier, axis=1).sum().sum()

    opt_costs_hv = pd.DataFrame(operating_costs_hv)
    opt_costs_hv.columns = ['operation_costs']
    opt_costs_hv['voltage_level'] = 'hv'
    # add df
    operating_costs = operating_costs.append(opt_costs_hv)

    tpc_ehv = pd.DataFrame(operating_costs_ehv.sum(),
                           columns=['operation_costs'],
                           index=['total_power_costs'])
    tpc_ehv['voltage_level'] = 'ehv'
    operating_costs = operating_costs.append(tpc_ehv)

    tpc_hv = pd.DataFrame(operating_costs_hv.sum(),
                          columns=['operation_costs'],
                          index=['total_power_costs'])
    tpc_hv['voltage_level'] = 'hv'
    operating_costs = operating_costs.append(tpc_hv)

    # add Grid and Transform Costs
    try:
        etg.lines['voltage_level'] = 'unknown'
        ix_ehv = etg.lines[etg.lines['v_nom'] >= 380].index
        etg.lines.set_value(ix_ehv, 'voltage_level', 'ehv')
        ix_hv = etg.lines[(etg.lines['v_nom'] <= 220) &
                          (etg.lines['v_nom'] >= 110)].index
        etg.lines.set_value(ix_hv, 'voltage_level', 'hv')

        losses_total = sum(etg.lines.losses) + sum(etg.transformers.losses)
        losses_costs = losses_total * np.average(etg.buses_t.marginal_price)

        # add Transform and Grid losses
        # etg.lines[['losses','voltage_level']].groupby('voltage_level',
        # axis=0).sum().reset_index()

    except AttributeError:
        logger.info("No Transform and Line losses are calcualted! \n"
                    "Use eTraGo pf_post_lopf method")
        losses_total = 0
        losses_costs = 0
    # total grid losses costs
    tgc = pd.DataFrame(losses_costs,
                       columns=['operation_costs'],
                       index=['total_grid_losses'])
    tgc['voltage_level'] = 'ehv/hv'
    operating_costs = operating_costs.append(tgc)

    #power_price = power_price.T.iloc[0]

    return operating_costs


def etrago_grid_investment(network, json_file, session):
    """ Function to get grid expantion costs from eTraGo

    Parameters
    ----------

    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    json_file : :obj:dict
        Dictionary of the ``scenario_setting.json`` file

    Returns
    -------
    grid_investment_costs : :pandas:`pandas.Dataframe<dataframe>`
        Dataframe with ``voltage_level``, ``number_of_expansion`` and
        ``capital_cost`` per calculated time steps

    Example
    -------

        .. code-block:: python

           >>> from ego.tools.io import eGo
           >>> ego = eGo(jsonpath='scenario_setting.json')
           >>> ego.etrago.grid_investment_costs

    +---------------+---------------+-------------------+--------------+
    |differentiation| voltage_level |number_of_expansion|  capital_cost|
    +===============+===============+===================+==============+
    | cross-border  |  ehv          |   27.0            | 31514.1305   |
    +---------------+---------------+-------------------+--------------+
    |  domestic     |  hv           |    0.0            |      0.0     |
    +---------------+---------------+-------------------+--------------+
    """

    # check settings for extendable
    if 'network' not in json_file['eTraGo']['extendable']:
        logger.info("The optimizition was not using parameter"
                    " 'extendable': network \n"
                    "No grid expantion costs from etrago")

    if 'network' in json_file['eTraGo']['extendable']:

        network = geolocation_buses(network, session)
        # differentiation by country_code

        network.lines['differentiation'] = 'none'

        network.lines['bus0_c'] = network.lines.bus0.map(
            network.buses.country_code)
        network.lines['bus1_c'] = network.lines.bus1.map(
            network.buses.country_code)

        for idx, val in network.lines.iterrows():

            check = val['bus0_c'] + val['bus1_c']

            if "DE" in check:
                network.lines['differentiation'][idx] = 'cross-border'
            if "DEDE" in check:
                network.lines['differentiation'][idx] = 'domestic'
            if "DE" not in check:
                network.lines['differentiation'][idx] = 'foreign'

        lines = network.lines[['v_nom', 'capital_cost', 's_nom',
                               's_nom_min', 's_nom_opt', 'differentiation']
                              ].reset_index()

        lines['s_nom_expansion'] = lines.s_nom_opt.subtract(
            lines.s_nom, axis='index')
        lines['capital_cost'] = lines.s_nom_expansion.multiply(
            lines.capital_cost, axis='index')
        lines['number_of_expansion'] = lines.s_nom_expansion > 0.0
        lines['time_step'] = get_time_steps(json_file)

        # add v_level
        lines['voltage_level'] = 'unknown'

        ix_ehv = lines[lines['v_nom'] >= 380].index
        lines.set_value(ix_ehv, 'voltage_level', 'ehv')

        ix_hv = lines[(lines['v_nom'] <= 220) & (lines['v_nom'] >= 110)].index
        lines.set_value(ix_hv, 'voltage_level', 'hv')

        # based on eTraGo Function:
        # https://github.com/openego/eTraGo/blob/dev/etrago/tools/utilities.py#L651
        # Definition https://pypsa.org/doc/components.html#line

        trafo = pd.DataFrame()
        # get costs of transfomers
        if json_file['eTraGo']['network_clustering_kmeans'] == False:

            network.transformers['differentiation'] = 'none'

            trafos = network.transformers[['v_nom0', 'v_nom1', 'capital_cost',
                                           's_nom_extendable', 's_nom',
                                           's_nom_opt']]

            trafos.columns.name = ""
            trafos.index.name = ""
            trafos.reset_index()

            trafos['s_nom_extendable'] = trafos.s_nom_opt.subtract(
                trafos.s_nom, axis='index')

            trafos['capital_cost'] = trafos.s_nom_extendable.multiply(
                trafos.capital_cost, axis='index')
            trafos['number_of_expansion'] = trafos.s_nom_extendable > 0.0
            trafos['time_step'] = get_time_steps(json_file)
            # add v_level
            trafos['voltage_level'] = 'unknown'

            # TODO check
            ix_ehv = trafos[trafos['v_nom0'] >= 380].index
            trafos.set_value(ix_ehv, 'voltage_level', 'ehv')

            ix_hv = trafos[(trafos['v_nom0'] <= 220) &
                           (trafos['v_nom0'] >= 110)].index
            trafos.set_value(ix_hv, 'voltage_level', 'hv')
            # aggregate trafo
            trafo = trafos[['voltage_level',
                            'capital_cost',
                            'differentiation']].groupby(['differentiation',
                                                         'voltage_level']
                                                        ).sum().reset_index()

        # aggregate lines
        line = lines[['voltage_level',
                      'capital_cost',
                      'differentiation']].groupby(['differentiation',
                                                   'voltage_level']
                                                  ).sum().reset_index()

        # merge trafos and line
        frames = [line, trafo]

        grid_investment_costs = pd.concat(frames)

        return grid_investment_costs

    # ToDo: add  .agg({'number_of_expansion':lambda x: x.count(),
    #  's_nom_expansion': np.sum,
    #  'grid_costs': np.sum})  <-  time_step
    pass


def edisgo_grid_investment(edisgo, json_file):
    """
    Function aggregates all costs, based on all calculated eDisGo
    grids and their weightings
    Parameters
    ----------
    edisgo : :class:`ego.tools.edisgo_integration.EDisGoNetworks`
        Contains multiple eDisGo networks
    Returns
    -------
    None or :pandas:`pandas.DataFrame<dataframe>`
        Dataframe containing annuity costs per voltage level
    """

    t = 40
    p = 0.05
    logger.info('For all components T={} and p={} is used'.format(t, p))

    costs = pd.DataFrame(
        columns=['voltage_level', 'annuity_costs', 'overnight_costs'])

    # Loop through all calculated eDisGo grids
    for key, value in edisgo.network.items():

        if not hasattr(value, 'network'):
            logger.warning('No results available for grid {}'.format(key))
            continue

        # eDisGo results (overnight costs) for this grid
        costs_single = value.network.results.grid_expansion_costs
        costs_single.rename(
            columns={'total_costs': 'overnight_costs'},
            inplace=True)

        # continue if this grid was not reinforced
        if (costs_single['overnight_costs'].sum() == 0.):
            logger.info('No expansion costs for grid {}'.format(key))
            continue

        # Overnight cost translated in annuity costs
        costs_single['capital_cost'] = edisgo_convert_capital_costs(
            costs_single['overnight_costs'],
            t=t,
            p=p,
            json_file=json_file)

        # Weighting (retrieves the singe (absolute) weighting for this grid)
        choice = edisgo.grid_choice
        weighting = choice.loc[
            choice['the_selected_network_id'] == key
        ][
            'no_of_points_per_cluster'
        ].values[0]

        costs_single[['capital_cost', 'overnight_costs']] = (
            costs_single[['capital_cost', 'overnight_costs']]
            * weighting)

        # Append costs of this grid
        costs = costs.append(
            costs_single[[
                'voltage_level',
                'capital_cost',
                'overnight_costs']], ignore_index=True)

    if len(costs) == 0:
        logger.info('No expansion costs in any MV grid')
        return None

    else:
        aggr_costs = costs.groupby(
            ['voltage_level']).sum().reset_index()

        # In eDisGo all costs are in kEuro (eGo only takes Euro)
        aggr_costs[['capital_cost', 'overnight_costs']] = (
            aggr_costs[['capital_cost', 'overnight_costs']]
            * 1000)

        successfull_grids = edisgo.successfull_grids
        if successfull_grids < 1:
            logger.warning(
                'Only {} % of the grids were calculated.\n'.format(
                    "{0:,.2f}".format(successfull_grids * 100)
                ) + 'Costs are extrapolated...')

            aggr_costs[['capital_cost', 'overnight_costs']] = (
                aggr_costs[['capital_cost', 'overnight_costs']]
                / successfull_grids)

    return aggr_costs


def get_generator_investment(network, scn_name):
    """ Get investment costs per carrier/ generator.

    """
    etg = network

    try:

        data = pkgutil.get_data('ego', 'data/investment_costs.csv')
        invest = pd.read_csv(io.BytesIO(data),
                             encoding='utf8', sep=",",
                             index_col="carriers")

    except FileNotFoundError:
        path = os.getcwd()
        filename = 'investment_costs.csv'
        invest = pd.DataFrame.from_csv(path + '/data/'+filename)

    if scn_name in ['SH Status Quo', 'Status Quo']:
        invest_scn = 'Status Quo'

    if scn_name in ['SH NEP 2035', 'NEP 2035']:
        invest_scn = 'NEP 2035'

    if scn_name in ['SH eGo 100', 'eGo 100']:
        invest_scn = 'eGo 100'

    gen_invest = pd.concat([invest[invest_scn],
                            etg.generators.groupby('carrier')['p_nom'].sum()],
                           axis=1, join='inner')

    gen_invest = pd.concat([invest[invest_scn], etg.generators.groupby(
        'carrier')
        ['p_nom'].sum()], axis=1, join='inner')
    gen_invest['carrier_costs'] = gen_invest[invest_scn] * \
        gen_invest['p_nom'] * 1000  # in MW

    return gen_invest
