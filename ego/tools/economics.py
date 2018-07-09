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

Todo:
 1) Investment costs of eTrago and eDisGo
 2) Total system costs
"""

import io
import os
import logging
logger = logging.getLogger('ego')

if not 'READTHEDOCS' in os.environ:
    import pandas as pd
    import numpy as np

__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität"\
    "Flensburg, Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolfbunke"

# calculate annuity per time step or periode


def annuity_per_period(capex, n, wacc, t):
    """
    Parameters
    ----------
    capex : float
        Capital expenditure (NPV of investment)
    n : int
        Number of years that the investment is used (economic lifetime)
    wacc : float
        Weighted average cost of capital

    ToDo
    ----
    t : int
        Timesteps in hours
    i : float
        interest rate
        ...
    """

    # ToDo change formular to hourly annuity costs
    return capex * (wacc * (1 + wacc) ** n) / ((1 + wacc) ** n - 1)


def etrago_operating_costs(network):
    """ Function to get all operating costs of eTraGo.

    Parameters
    ----------
    network : Network of eTraGo
        Network of eTraGo

    Returns
    -------
    power_price :  :class:`~.pd.DataFrame`

    Examples
    --------

    - losses
    - grid losses : amount and costs
    - use calc_line_losses(network)  from etrago pf_post_lopf

    ToDo
    ----
    - change naming and function structure
    - seperate operation costs in other functions ?

    """
    etg = network
    #etg = eTraGo
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


def etrago_grid_investment(network):
    """ Function to get grid expantion costs form etrago

    Parameters
    ----------

    network : Network
        eTraGo

    Returns
    -------

    ToDo
    ----
    - add new release of etrago 0.7
    """

    pass


def edisgo_grid_investment(network):
    """Function to get all costs of grid investment of eDisGo.

    Notes
    -----
    - ToDo add iteration and container of all costs of edisgo network
    """
    pass


def get_generator_investment(network, scn_name):
    """ Get investment costs per carrier/gernator.

    work around later db table ->  check capital_cost as cost input?!?

    ToDo
    ----
    - change values in csv
    - add values to database

    """
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
    """
    Return pandas DataFrame with investment costs of

    etrago:
    Storages
    Line extentation

    edisgo:
    Line extentation
    Storage costs?

    ToDo
    ----
    - add edisgo

    """
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
