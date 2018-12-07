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
"""
This files contains all eGo interface functions
"""

__copyright__ = ("Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc"

# Import
# General Packages
import os
import pandas as pd
import time
if not 'READTHEDOCS' in os.environ:
    from egoio.db_tables import model_draft
    from egoio.db_tables import supply
    import math

import logging
logger = logging.getLogger(__name__)


# Functions

def get_etragospecs_direct(session,
                           bus_id,
                           etrago_network,
                           scn_name,
                           grid_version,
                           pf_post_lopf,
                           max_cos_phi_renewable):
    """
    Reads eTraGo Results from Database and returns and returns
    the interface values as a dictionary of corresponding dataframes

    Parameters
    ----------
    session : sqlalchemy.orm.session.Session
        Handles conversations with the database.
    bus_id : int
        ID of the corresponding HV bus
    etrago_network: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    scn_name : str
        Name of used scenario 'Status Quo', 'NEP 2035' or 'eGo 100'


    Returns
    -------
    :obj:`dict` of :pandas:`pandas.DataFrame<dataframe>`
        Dataframes used as eDisGo inputs

    """
    logger.info('Specs for bus {}'.format(bus_id))
    if pf_post_lopf:
        logger.info('Active and reactive power interface')
    else:
        logger.info('Only active power interface')

    specs_meta_data = {}
    performance = {}

    specs_meta_data.update({'TG Bus ID': bus_id})

    if grid_version is None:
        logger.warning('Weather_id taken from model_draft (not tested)')

        ormclass_gen_single = model_draft.__getattribute__(
            'EgoSupplyPfGeneratorSingle')
    else:
        ormclass_aggr_w = supply.__getattribute__(
            'EgoAggrWeather')

    snap_idx = etrago_network.snapshots

    # Generators
    t0 = time.perf_counter()

    weather_dpdnt = ['wind', 'solar', 'wind_onshore', 'wind_offshore']

    # DF procesing
    all_gens_df = etrago_network.generators[
        etrago_network.generators['bus'] == str(bus_id)
    ]
    all_gens_df.index.name = 'generator_id'

    all_gens_df.reset_index(inplace=True)

    all_gens_df = all_gens_df[[
        'generator_id',
        'p_nom',
        'p_nom_opt',
        'carrier']]

    all_gens_df = all_gens_df.rename(columns={"carrier": "name"})

    all_gens_df = all_gens_df[all_gens_df['name'] != 'wind_offshore']

    for index, row in all_gens_df.iterrows():
        name = row['name']
        if name == 'wind_onshore':
            all_gens_df.at[index, 'name'] = 'wind'

    # Conventionals
    t1 = time.perf_counter()
    performance.update({'Generator Data Processing': t1-t0})

    conv_df = all_gens_df[~all_gens_df.name.isin(weather_dpdnt)]

    conv_dsptch = pd.DataFrame(0.0,
                               index=snap_idx,
                               columns=list(set(conv_df['name'])))
    conv_reactive_power = pd.DataFrame(0.0,
                                       index=snap_idx,
                                       columns=list(set(conv_df['name'])))

    if not conv_df.empty:
        conventionals = True
        conv_cap = conv_df[['p_nom', 'name']].groupby('name').sum().T

        for index, row in conv_df.iterrows():
            generator_id = row['generator_id']
            source = row['name']
            p = etrago_network.generators_t.p[str(generator_id)]
            p_norm = p / conv_cap[source]['p_nom']
            conv_dsptch[source] = conv_dsptch[source] + p_norm
            if pf_post_lopf:
                q = etrago_network.generators_t.q[str(generator_id)]
                # q normalized with p_nom
                q_norm = q / conv_cap[source]['p_nom']
                conv_reactive_power[source] = (
                    conv_reactive_power[source]
                    + q_norm)

        if pf_post_lopf:
            new_columns = [
                (col, '') for col in conv_reactive_power.columns
            ]
            conv_reactive_power.columns = pd.MultiIndex.from_tuples(
                new_columns)

    else:
        conventionals = False
        logger.warning('No conventional generators at bus {}'.format(bus_id))

    # Renewables
    t2 = time.perf_counter()
    performance.update({'Conventional Dispatch': t2-t1})
    # Capacities
    ren_df = all_gens_df[all_gens_df.name.isin(weather_dpdnt)]
    if ren_df.empty:
        logger.warning('No renewable generators at bus {}'.format(bus_id))

    for index, row in ren_df.iterrows():
        aggr_id = row['generator_id']
        if grid_version is None:
            w_id = session.query(
                ormclass_gen_single.w_id
            ).filter(
                ormclass_gen_single.aggr_id == aggr_id,
                ormclass_gen_single.scn_name == scn_name
            ).limit(1).scalar()
        else:
            w_id = session.query(
                ormclass_aggr_w.w_id
            ).filter(
                ormclass_aggr_w.aggr_id == aggr_id,
                #ormclass_aggr_w.scn_name == scn_name,
                ormclass_aggr_w.version == grid_version
            ).limit(1).scalar()

        ren_df.at[index, 'w_id'] = w_id

    ren_df.dropna(inplace=True)

    aggr_gens = ren_df.groupby([
        'name',
        'w_id'
    ]).agg({'p_nom': 'sum'}).reset_index()

    aggr_gens.rename(columns={'p_nom': 'p_nom_aggr'}, inplace=True)

    aggr_gens['ren_id'] = aggr_gens.index

    ### Dispatch and Curteilment
    potential = pd.DataFrame(0.0,
                             index=snap_idx,
                             columns=aggr_gens['ren_id'])
    dispatch = pd.DataFrame(0.0,
                            index=snap_idx,
                            columns=aggr_gens['ren_id'])
    curtailment = pd.DataFrame(0.0,
                               index=snap_idx,
                               columns=aggr_gens['ren_id'])
    if pf_post_lopf:
        reactive_power = pd.DataFrame(0.0,
                                      index=snap_idx,
                                      columns=aggr_gens['ren_id'])

    for index, row in ren_df.iterrows():
        gen_id = row['generator_id']
        name = row['name']
        w_id = row['w_id']
        ren_id = int(aggr_gens[
            (aggr_gens['name'] == name) &
            (aggr_gens['w_id'] == w_id)]['ren_id'])

        p_nom_aggr = float(
            aggr_gens[aggr_gens['ren_id'] == ren_id]['p_nom_aggr'])
        p_nom = row['p_nom']

        p_series = etrago_network.generators_t.p[str(gen_id)]
        p_norm_tot_series = p_series / p_nom_aggr

        p_max_pu_series = etrago_network.generators_t.p_max_pu[str(gen_id)]
        p_max_norm_tot_series = p_max_pu_series * p_nom / p_nom_aggr

        potential[ren_id] = potential[ren_id] + p_max_norm_tot_series
        dispatch[ren_id] = dispatch[ren_id] + p_norm_tot_series

        if pf_post_lopf:
            q_series = etrago_network.generators_t.q[str(gen_id)]
            q_norm_tot_series = q_series / p_nom_aggr
            reactive_power[ren_id] = (
                reactive_power[ren_id]
                + q_norm_tot_series)

    curtailment = potential.sub(dispatch)

    new_columns = [
        (aggr_gens[aggr_gens.ren_id == col].name.iloc[0],
         aggr_gens[aggr_gens.ren_id == col].w_id.iloc[0])
        for col in potential.columns]
    potential.columns = pd.MultiIndex.from_tuples(new_columns)

    new_columns = [
        (aggr_gens[aggr_gens.ren_id == col].name.iloc[0],
         aggr_gens[aggr_gens.ren_id == col].w_id.iloc[0])
        for col in dispatch.columns]
    dispatch.columns = pd.MultiIndex.from_tuples(new_columns)

    new_columns = [
        (aggr_gens[aggr_gens.ren_id == col].name.iloc[0],
         aggr_gens[aggr_gens.ren_id == col].w_id.iloc[0])
        for col in curtailment.columns]
    curtailment.columns = pd.MultiIndex.from_tuples(new_columns)

    if pf_post_lopf:
        new_columns = [
            (aggr_gens[aggr_gens.ren_id == col].name.iloc[0],
             aggr_gens[aggr_gens.ren_id == col].w_id.iloc[0])
            for col in reactive_power.columns]
        reactive_power.columns = pd.MultiIndex.from_tuples(new_columns)

        # Q limit calculation
        if max_cos_phi_renewable:
            logger.info('Applying Q limit (max cos(phi)={})'.format(
                max_cos_phi_renewable))

            phi = math.acos(max_cos_phi_renewable)

            for col in reactive_power:
                for idx in reactive_power.index:
                    p = dispatch.loc[idx][col]
                    q = reactive_power.loc[idx][col]

                    q_max, q_min = p * math.tan(phi), -p * math.tan(phi)

                    if q > q_max:
                        q = q_max
                    elif q < q_min:
                        q = q_min

                    reactive_power.at[idx, col] = q

        # Reactive Power concat
        if conventionals:
            all_reactive_power = pd.concat([
                conv_reactive_power,
                reactive_power], axis=1)
        else:
            all_reactive_power = reactive_power

    # Storage
    t3 = time.perf_counter()
    performance.update({'Renewable Dispatch and Curt.': t3-t2})
    # Capactiy
    min_extended = 0.3
    stor_df = etrago_network.storage_units.loc[
        (etrago_network.storage_units['bus'] == str(bus_id))
        & (etrago_network.storage_units['p_nom_extendable'] == True)
        & (etrago_network.storage_units['p_nom_opt'] > min_extended)
        & (etrago_network.storage_units['max_hours'] <= 20.)]  # Only batteries

    logger.warning('Minimum storage of {} MW'.format(min_extended))

    ext_found = False
    if len(stor_df) == 1:
        logger.info('Extendable storage unit found')
        ext_found = True

        stor_id = stor_df.index[0]

        stor_p_series_kW = etrago_network.storage_units_t.p[
            str(stor_id)] * 1000

        if pf_post_lopf:
            try:
                stor_q_series_kvar = etrago_network.storage_units_t.q[
                    str(stor_id)] * 1000
            except:
                logger.warning("No Q series found for storage unit {}".format(
                    stor_id))
                stor_q_series_kvar = etrago_network.storage_units_t.p[
                    str(stor_id)] * 0

    if ext_found == False:
        logger.info(
            "No extendable storage unit found at bus {}".format(bus_id))

    t4 = time.perf_counter()
    performance.update({'Storage Data Processing and Dispatch': t4-t3})

    specs = {
        'conv_dispatch': conv_dsptch,
        'ren_dispatch': dispatch,
        'ren_potential': potential,
        'ren_curtailment': curtailment
    }

    if ext_found:
        specs['battery_p_series'] = stor_p_series_kW

        if pf_post_lopf:
            specs['battery_q_series'] = stor_q_series_kvar

    else:
        specs['battery_p_series'] = specs['battery_q_series'] = None

    if pf_post_lopf:
        specs['reactive_power'] = all_reactive_power

    t5 = time.perf_counter()
    performance.update({'Overall time': t5-t0})

    return specs
