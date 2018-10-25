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
"""This module include the results functions for analyze and creating results
based on eTraGo or eDisGo for eGo.
"""
# TODO  - write results to database

import io
import os
import logging
logger = logging.getLogger('ego')

if not 'READTHEDOCS' in os.environ:
    import pandas as pd
    import numpy as np
    from ego.tools.economics import get_generator_investment

__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität"\
    "Flensburg, Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolfbunke"


def create_etrago_results(network, scn_name):  # rename function
    """
    Create eTraGo results

    Parameters
    ----------
    network : :class:`~.etrago.tools.io.NetworkScenario`
        eTraGo ``NetworkScenario`` based on PyPSA Network. See also
        `pypsa.network <https://pypsa.org/doc/components.html#network>`_

    scn_name : str
        Name of used scenario


    Returns
    -------
    generator :  :pandas:`pandas.DataFrame<dataframe>`
        Result of generator as DataFrame in ``ego.etrago.generator``

    """

    etg = network
    etrago = pd.DataFrame()

    etrago['p_nom'] = etg.generators.groupby('carrier')['p_nom'].sum()  # in MW
    etrago['p_nom_opt'] = etg.generators.groupby('carrier')[
        'p_nom_opt'].sum()  # in MW
    #  power price
    etrago['marginal_cost'] = etg.generators.groupby('carrier'
                                                     )['marginal_cost'].mean()
    # in in [EUR]

    # get power price by production MWh _t.p * marginal_cost
    power_price = etg.generators_t.p[etg.generators[etg.generators.
                                                    control != 'Slack']
                                     .index] * etg.generators.\
        marginal_cost[etg.generators[etg.generators.
                                     control != 'Slack'].index]  # without Slack

    power_price = power_price.groupby(
        etg.generators.carrier, axis=1).sum().sum()
    etrago['power_price'] = power_price

    # use country code
    p_by_carrier = pd.concat([etg.generators_t.p
                              [etg.generators[etg.generators.control !=
                                              'Slack'].index],
                              etg.generators_t.p[etg.generators[
                                  etg.
                                  generators.control == 'Slack'].index
                              ].iloc[:, 0].
                              apply(lambda x: x if x > 0 else 0)], axis=1).\
        groupby(etg.generators.carrier, axis=1).sum()  # in MWh

    etrago['p'] = p_by_carrier.sum()
    # add invetment
    result_invest = get_generator_investment(network, scn_name)

    etrago = etrago.assign(investment_costs=result_invest['carrier_costs'])

    return etrago


if __name__ == '__main__':
    pass
