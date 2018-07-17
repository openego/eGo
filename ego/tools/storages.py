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
"""This module contains functions to summarize and studies on storages.
"""

import io
import os
import logging
logger = logging.getLogger('ego')

if not 'READTHEDOCS' in os.environ:
    import pandas as pd
    import numpy as np

__copyright__ = ("Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc"


def total_storage_charges(network):
    """Sum up the pysical storage values of the total scenario based on
    eTraGo results.

    Parameters
    ----------
    network : :class:`etrago.tools.io.NetworkScenario`
        eTraGo ``NetworkScenario`` based on PyPSA Network. See also
        `pypsa.network <https://pypsa.org/doc/components.html#network>`_

    Returns
    -------
    results : :pandas:`pandas.DataFrame<dataframe>`
        Summarize and returns a ``DataFrame`` of the storages optimaziation.

    Notes
    -----

    The ``results`` dataframe inclueds following parameters:

    charge : numeric
         Quantity of charged Energy in MWh over scenario time steps
    discharge : numeric
        Quantity of discharged Energy in MWh over scenario time steps
    count : int
        Number of storage units
    p_nom_o_sum: numeric
        Sum of optimal installed power capacity
    """

    charge = network.storage_units_t.\
        p[network.storage_units_t.p[network.
                                    storage_units[network.storage_units.
                                                  p_nom_opt > 0].index].
          values > 0.].groupby(network.storage_units.
                               carrier, axis=1).sum().sum()

    discharge = network.storage_units_t.p[network.storage_units_t.
                                          p[network.
                                            storage_units[network.storage_units.
                                                          p_nom_opt > 0].
                                            index].values < 0.].\
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
    """Using function ``total_storage_charges`` for storage and grid expantion
    costs of eTraGo.

    Parameters
    ----------
    network : :class:`etrago.tools.io.NetworkScenario`
        eTraGo ``NetworkScenario`` based on PyPSA Network. See also
        `pypsa.network <https://pypsa.org/doc/components.html#network>`_

    Returns
    -------
    storages : :pandas:`pandas.DataFrame<dataframe>`
        DataFrame with cumulated results of storages

    """
    # Charge / discharge (MWh) and installed capacity MW
    storages = total_storage_charges(network=network)

    return storages


def etrago_storages_investment(network):
    """Calculate storage investment costs of eTraGo

    Parameters
    ----------
    network : :class:`etrago.tools.io.NetworkScenario`
        eTraGo ``NetworkScenario`` based on PyPSA Network. See also
        `pypsa.network <https://pypsa.org/doc/components.html#network>`_


    Returns
    -------
    storage_costs : numeric
        Storage costs of selected snapshots in [EUR]

    """
    # provide storage installation costs
    if sum(network.storage_units.p_nom_opt) != 0:
        installed_storages = \
            network.storage_units[network.storage_units.p_nom_opt != 0]
        storage_costs = sum(
            installed_storages.capital_cost *
            installed_storages.p_nom_opt)
        print(
            "Investment costs for all storages in selected snapshots [EUR]:",
            round(
                storage_costs,
                2))
    return storage_costs
