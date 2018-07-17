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
"""This module collects useful functions for economic calculation of eGo which can
mainly distinguished in operational and investment costs.
"""

import io
import os
import logging
logger = logging.getLogger('ego')

if not 'READTHEDOCS' in os.environ:
    import pandas as pd
    import numpy as np
    from tools.utilities import get_time_steps

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


# grid_components = {"hv_mv_transformer": "40 MVA", "mv_lv_transformer": "630 kVA",
#                   "mv_line": "NA2XS2Y 3x1x185 RM/25", "lv_line": "NAYY 4x1x150"}
# json_file = ego.json_file
# cost_config = {"p": 0.04}


def edisgo_convert_capital_costs(grid_components, cost_config, json_file):
    """ Get scenario and calculation specific annuity cost by given capital
    costs and lifetime.


    Parameters
    ----------
    grid_components : :obj:dict
        Dictionary of ding0 grid components which are extendable
        (Name, investment_cost, lifetime)
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
    annuity_cost : numeric
        Scenario and calculation specific annuity cost by given capital
        costs and lifetime

    Examples
    --------
    .. math::

        PVA =   (1 / p) - (1 / (p*(1 + p)^T))

    """
    # Based on eTraGo calculation in
    # https://github.com/openego/eTraGo/blob/dev/etrago/tools/utilities.py#L651

    T = 40  # from grid_components ?
    p = cost_config['p']

    # Calculate present value of an annuity (PVA)
    PVA = (1 / p) - (1 / (p*(1 + p) ** T))

    year = 8760
    # get period of calculation
    period = (json_file['eTraGo']['start_snapshot']
              - json_file['eTraGo']['start_snapshot'])

    # calculation of capital_cost
    annuity_cost = (capital_cost / (PVA * (year/(period+1))))

    return annuity_cost


def etrago_operating_costs(network):
    """ Function to get all operating costs of eTraGo.

    Parameters
    ----------
    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`

    Returns
    -------
    power_price :  :pandas:`pandas.Dataframe<dataframe>`

    Examples
    --------

    - losses
    - grid losses : amount and costs
    - use calc_line_losses(network)  from etrago pf_post_lopf

    """
    # TODO   - change naming and function structure
    # TODO    - seperate operation costs in other functions ?

    etg = network
    # etg = eTraGo
    # groupby v_nom
    power_price = etg.generators_t.p[etg.generators[etg.generators.
                                                    control != 'Slack'].index] * etg.generators.\
        marginal_cost[etg.generators[etg.generators.
                                     control != 'Slack'].index]  # without Slack

    power_price = power_price.groupby(
        etg.generators.carrier, axis=1).sum().sum()
    power_price

    etg.buses_t.marginal_price
    etg.buses_t['p'].sum().sum()

    # active power x nodel price /
    etg.lines_t['p0'].sum().sum()
    etg.lines_t['p1'].sum().sum()
    # Reactive power
    etg.lines_t['q0'].sum().sum()
    etg.lines_t['q1'].sum().sum()

    # currency/MVA ? wie berechnen

    etg.lines_t['mu_lower'].sum().sum()

    etg.lines['s_nom'].sum()

    etg.lines_t['mu_upper'].sum().sum()

    return power_price


def etrago_grid_investment(network, json_file):
    """ Function to get grid expantion costs form etrago

    Parameters
    ----------

    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    json_file : :obj:dict
        Dictionary of the ``scenario_setting.json`` file

    Returns
    -------
    lines: :pandas:`pandas.Dataframe<dataframe>`
        Dataframe with ``number_of_expansion``, ``s_nom_expansion`` and
        ``grid_costs`` per calculated time steps

    Example
    -------

        .. code-block:: python

           >>> from ego.tools.io import eGo
           >>> ego = eGo(jsonpath='scenario_setting.json')
           >>> ego.etrago.grid_costs

    +--------+-------------------+------------+
    | v_level|number_of_expansion|  grid_costs|
    +========+===================+============+
    |  ehv   |   27.0            | 31514.1305 |
    +--------+-------------------+------------+
    |  hv    |    0.0            |      0.0   |
    +--------+-------------------+------------+
    """

    # check settings for extendable
    if 'network' not in json_file['eTraGo']['extendable']:
        print("The optimizition was not using parameter 'extendable': network")
        print("No grid expantion costs from etrago")

    if 'network' in json_file['eTraGo']['extendable']:

        lines = network.lines[['v_nom', 'capital_cost', 's_nom',
                               's_nom_min', 's_nom_opt']].reset_index()

        lines['s_nom_expansion'] = lines.s_nom_opt.subtract(
            lines.s_nom, axis='index')
        lines['grid_costs'] = lines.s_nom_expansion.multiply(
            lines.capital_cost, axis='index')
        lines['number_of_expansion'] = lines.s_nom_expansion > 0.0
        lines['time_step'] = get_time_steps(json_file)

        # add v_level
        lines['v_level'] = 'unknown'

        ix_ehv = lines[lines['v_nom'] >= 380].index
        lines.set_value(ix_ehv, 'v_level', 'ehv')

        ix_hv = lines[(lines['v_nom'] <= 220) & (lines['v_nom'] >= 110)].index
        lines.set_value(ix_hv, 'v_level', 'hv')

        # based on eTraGo Function:
        # https://github.com/openego/eTraGo/blob/dev/etrago/tools/utilities.py#L651
        # Definition https://pypsa.org/doc/components.html#line

        # get costs of transfomers
        trafos = network.transformers[['v_nom0', 'v_nom1', 'capital_cost',
                                       's_nom_extendable', 's_nom',
                                       's_nom_opt']].reset_index()

        trafos['s_nom_extendable'] = trafos.s_nom_opt.subtract(
            trafos.s_nom, axis='index')
        trafos['grid_costs'] = trafos.s_nom_extendable.multiply(
            trafos.capital_cost, axis='index')
        trafos['number_of_expansion'] = trafos.s_nom_extendable > 0.0
        trafos['time_step'] = get_time_steps(json_file)

        # add v_level
        trafos['v_level'] = 'unknown'

        # TODO check
        ix_ehv = trafos[trafos['v_nom0'] >= 380].index
        trafos.set_value(ix_ehv, 'v_level', 'ehv')

        ix_hv = trafos[(trafos['v_nom0'] <= 220) &
                       (trafos['v_nom0'] >= 110)].index
        trafos.set_value(ix_hv, 'v_level', 'hv')

        # aggregate lines and trafo
        line = lines[['v_level', 'number_of_expansion',
                      'grid_costs']].groupby('v_level').sum().reset_index()

        trafo = trafos[['v_level', 'number_of_expansion',
                        'grid_costs']].groupby('v_level').sum().reset_index()

        # merge trafos and line
        frames = [line, trafo]

        result = pd.concat(frames)

        return result

    # ToDo: add  .agg({'number_of_expansion':lambda x: x.count(),
    #  's_nom_expansion': np.sum,
    #  'grid_costs': np.sum})  <-  time_step
    pass


def edisgo_grid_investment(network_edisgo):
    """Function to get all costs of grid investment of eDisGo.

    Parameters
    ----------

    network_edisgo : :pandas:`pandas.Dataframe<dataframe>`
        Network container of eDisGo


    """

    pass


def get_generator_investment(network, scn_name):
    """ Get investment costs per carrier/gernator.

    work around later db table ->  check capital_cost as cost input?!?
    """
    # TODO   - change values in csv
    #        - add values to database

    etg = network

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

    gen_invest = pd.concat([invest[invest_scn], etg.generators.groupby('carrier')
                            ['p_nom'].sum()], axis=1, join='inner')
    gen_invest['carrier_costs'] = gen_invest[invest_scn] * \
        gen_invest['p_nom'] * 1000  # in MW

    return gen_invest


def investment_costs(network):
    """Return pandas DataFrame with investment costs of

    etrago:
    Storages
    Line extentation

    edisgo:
    Line extentation
    Storage costs?

    """
    # TODO  add edisgo

    etg = network
    invest = pd.DataFrame()

    # storages
    # get total storage investment costs
    # unit of costs?
    installed_storages = etg.storage_units[etg.storage_units.p_nom_opt != 0]
    costs = sum(installed_storages.capital_cost * installed_storages.p_nom_opt)
    invest = invest.append({'storage_costs': costs}, ignore_index=True)

    #  get storage costs per voltage level
    loc = etg.storage_units[etg.storage_units.p_nom_opt != 0]['bus']
    v_level = etg.buses.loc[loc, :]['v_nom']
    installed_storages = installed_storages.assign(v_nom=0)

    for i, k in v_level.iteritems():
        installed_storages.loc[installed_storages[installed_storages.bus ==
                                                  i].index, 'v_nom'] = k

    storage_level = installed_storages.groupby('v_nom')['capital_cost'].sum()

    # Line extentation costs
    # (eTraGo.lines.s_nom_opt -  eTraGo.lines.s_nom) * eTraGo.lines.capital_cost
    line_expen = (etg.lines.groupby('v_nom')['s_nom_opt'].sum()
                  - etg.lines.groupby('v_nom')['s_nom'].sum())

    if line_expen.sum() <= 0:
        print('Warning: !line extentation, set random costs for plotting!')

        lines_level = pd.DataFrame([[110., 722*np.exp(8)], [220., 822*np.exp(8)],
                                    [380., 999*np.exp(9)]], columns=['v_nom', 'capital_cost']).\
            groupby('v_nom')['capital_cost'].sum()

    invest = invest.assign(line_costs=lines_level.sum())

    # invest.transpose()

    # transfomers expantion costs
    return invest
