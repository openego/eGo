# -*- coding: utf-8 -*-
"""
Module of eGo results with functions for writing, creating and results of eGo

ToDo
----
 - add eDisGo
 - write results to database
 - integrate plot and other functions ad methods to the class eGo


"""
__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität"\
    "Flensburg, Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolfbunke"

import io
import os
import logging
logger = logging.getLogger('ego')

if not 'READTHEDOCS' in os.environ:
    import pandas as pd
    import numpy as np
    from etrago.tools.plot import (plot_line_loading, plot_stacked_gen,
                                   curtailment, gen_dist,
                                   storage_distribution,
                                   plot_voltage, plot_residual_load)


def total_storage_charges(network):
    """
    Sum up the pysical storage values of the total scenario based on
    eTraGo results.

    Parameters
    ----------
    network : eTraGo Network based on pypsa.network
        PyPSA Network object modified by eTraGo

    plot (bool):
        Use plot function


    Returns
    -------

    results : pandas.DataFrame
        Return ...

    Notes
    -----
    charge :
         Quantity of charged Energy in MWh over scenario time steps

    discharge :
        Quantity of discharged Energy in MWh over scenario time steps

    count :
        Number of storage units

    p_nom_o_sum:
        Sum of optimal installed power capacity
    """

    charge = network.storage_units_t.p[network.storage_units_t.
                                       p[network.storage_units[network.storage_units.
                                                               p_nom_opt > 0].index].values > 0.].\
        groupby(network.storage_units.carrier, axis=1).sum().sum()

    discharge = network.storage_units_t.p[network.storage_units_t.
                                          p[network.storage_units[network.storage_units.
                                                                  p_nom_opt > 0].index].values < 0.].\
        groupby(network.storage_units.carrier, axis=1).sum().sum()

    count = network.storage_units.bus[network.storage_units.p_nom_opt > 0].\
        groupby(network.storage_units.carrier, axis=0).count()

    p_nom_sum = network.storage_units.p_nom.groupby(network.storage_units.
                                                    carrier, axis=0).sum()

    p_nom_o_sum = network.storage_units.p_nom_opt.groupby(network.storage_units.
                                                          carrier, axis=0).sum()
    p_nom_o = p_nom_sum - p_nom_o_sum  # Zubau

    results = pd.concat([charge.rename('charge'), discharge.rename('discharge'),
                         p_nom_sum, count.rename('total_units'), p_nom_o
                         .rename('extension'), ], axis=1, join='outer')

    return results


def etrago_storages(network):
    """Function for storage and grid expantion costs of eTraGo.

    Parameters
    ----------

    network : eTraGo Network
        eTraGo Network Class based on PyPSA

    Returns
    -------
    storages : pandas.DataFrame
        DataFrame with cumulated results of storages

    """
    # Charge / discharge (MWh) and installed capacity MW
    storages = total_storage_charges(network=network)

    return storages


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


def create_etrago_results(network, scn_name):
    """
    Create eTraGo results

    Returns
    -------
    etrago :  :obj:pd.DataFrame

    """

    etg = network
    etrago = pd.DataFrame()

    etrago['p_nom'] = etg.generators.groupby('carrier')['p_nom'].sum()  # in MW
    etrago['p_nom_opt'] = etg.generators.groupby('carrier')[
        'p_nom_opt'].sum()  # in MW
    #  power price
    etrago['marginal_cost'] = etg.generators.groupby('carrier'
                                                     )['marginal_cost'].mean()  # in in [EUR]

    # get power price by production MWh _t.p * marginal_cost
    power_price = etg.generators_t.p[etg.generators[etg.generators.
                                                    control != 'Slack'].index] * etg.generators.\
        marginal_cost[etg.generators[etg.generators.
                                     control != 'Slack'].index]  # without Slack

    power_price = power_price.groupby(
        etg.generators.carrier, axis=1).sum().sum()
    etrago['power_price'] = power_price

    # use country code
    p_by_carrier = pd.concat([etg.generators_t.p
                              [etg.generators[etg.generators.control != 'Slack'].index],
                              etg.generators_t.p[etg.generators[etg.
                                                                generators.control == 'Slack'].index].iloc[:, 0].
                              apply(lambda x: x if x > 0 else 0)], axis=1).\
        groupby(etg.generators.carrier, axis=1).sum()  # in MWh

    etrago['p'] = p_by_carrier.sum()
    # add invetment
    result_invest = get_generator_investment(network, scn_name)

    etrago = etrago.assign(investment_costs=result_invest['carrier_costs'])

    return etrago


if __name__ == '__main__':
    pass
