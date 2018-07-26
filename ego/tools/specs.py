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
    #    from sqlalchemy import distinct
    # This gives me the specific ORM classes.
    from egoio.db_tables import model_draft
#    from edisgo.grid.network import ETraGoSpecs

import logging
logger = logging.getLogger(__name__)


# Functions

# def get_etragospecs_from_db(session,
#                            bus_id,
#                            result_id):
#    """
#    Reads eTraGo Results from Database and returns an Object of the Interface class ETraGoSpecs
#
#    Parameters
#    ----------
#    session : :class:`~.` #Todo: Add class etc....
#        Oemof session object (Database Interface)
#    bus_id : int
#        ID of the corresponding HV bus
#    result_id : int
#        ID of the corresponding database result
#
#
#    Returns
#    -------
#    etragospecs : :class:~.`
#        eDisGo ETraGoSpecs Object
#
#    """
#    print("\nSpecs from DB")
#    specs_meta_data = {}
#    performance = {}
#
#    specs_meta_data.update({'TG Bus ID': bus_id})
#    specs_meta_data.update({'Result ID': result_id})
#
#    # Mapping
#    ormclass_result_meta = model_draft.__getattribute__('EgoGridPfHvResultMeta')
#    # Instead of using the automapper, this is the explicit alternative (from egoei.db_tables).
#    ormclass_result_bus = model_draft.__getattribute__('EgoGridPfHvResultBus')
#    # ormclass_result_bus = model_draft.EgoGridPfHvResultBus # This is equivalent
#    #ormclass_result_bus_t = model_draft.__getattribute__('EgoGridPfHvResultBusT')
#    ormclass_result_gen = model_draft.__getattribute__(
#        'EgoGridPfHvResultGenerator')
#    ormclass_result_gen_t = model_draft.__getattribute__(
#        'EgoGridPfHvResultGeneratorT')
#    #ormclass_result_gen_single = model_draft.__getattribute__('EgoSupplyPfGeneratorSingle')
#    #ormclass_result_load = model_draft.__getattribute__('EgoGridPfHvResultLoad')
#    #ormclass_result_load_t = model_draft.__getattribute__('EgoGridPfHvResultLoadT')
#    ormclass_result_stor = model_draft.__getattribute__(
#        'EgoGridPfHvResultStorage')
#    ormclass_result_stor_t = model_draft.__getattribute__(
#        'EgoGridPfHvResultStorageT')
#    ormclass_source = model_draft.__getattribute__('EgoGridPfHvSource')
#    ormclass_aggr_w = model_draft.__getattribute__(
#        'ego_supply_aggr_weather_mview')
#
#    # Meta Queries
#    # Check
#
#    if session.query(ormclass_result_bus).filter(
#            ormclass_result_bus.bus_id == bus_id,
#            ormclass_result_bus.result_id == result_id
#    ).count() == 0:
#        logger.warning('Bus not found')
#
#    # Snapshot Range
#
#    snap_idx = session.query(
#        ormclass_result_meta.snapshots
#    ).filter(
#        ormclass_result_meta.result_id == result_id
#    ).scalar(
#    )
#
#    scn_name = session.query(
#        ormclass_result_meta.scn_name
#    ).filter(
#        ormclass_result_meta.result_id == result_id
#    ).scalar(
#    )
#    if scn_name == 'SH Status Quo':
#        scn_name = 'Status Quo'
#
#    specs_meta_data.update({'scn_name': scn_name})
#
#    # Generators
#
#    try:
#        t0 = time.perf_counter()
#        weather_dpdnt = ['wind', 'solar']
#    # Conventionals
#        t1 = time.perf_counter()
#        performance.update({'Generator Data Processing': t1-t0})
#
#        query = session.query(
#            # This ID is an aggregate ID (single generators aggregated)
#            ormclass_result_gen.generator_id,
#            ormclass_result_gen.p_nom,
#            ormclass_source.name
#        ).join(
#            ormclass_source,
#            ormclass_source.source_id == ormclass_result_gen.source
#        ).filter(
#            ormclass_result_gen.bus == bus_id,
#            ormclass_result_gen.result_id == result_id,
#            ormclass_source.name.notin_(weather_dpdnt))
#
#        conv_df = pd.DataFrame(query.all(),
#                               columns=[column['name'] for
#                                        column in
#                                        query.column_descriptions])
#
#        conv_cap = conv_df[['p_nom', 'name']].groupby('name').sum().T
#
#        query = session.query(
#            ormclass_result_gen_t.generator_id,
#            ormclass_result_gen_t.p
#        ).filter(
#            ormclass_result_gen_t.generator_id.in_(conv_df['generator_id']),
#            ormclass_result_gen_t.result_id == result_id
#        )
#
#        conv_t_df = pd.DataFrame(query.all(),
#                                 columns=[column['name'] for column in query.column_descriptions])
#
#        conv_t_df = pd.merge(conv_df,
#                             conv_t_df,
#                             on='generator_id')[[
#                                 'name',
#                                 'p']]
#
#        conv_dsptch_norm = pd.DataFrame(0.0,
#                                        index=snap_idx,
#                                        columns=list(set(conv_df['name'])))
#
#        for index, row in conv_t_df.iterrows():
#            source = row['name']
#            gen_series_norm = pd.Series(
#                # Every generator normalized by installed capacity.
#                data=(row['p'] / conv_cap[source]['p_nom']),
#                index=snap_idx)
#            conv_dsptch_norm[source] = conv_dsptch_norm[source] + \
#                gen_series_norm
#
#    # Renewables
#        t2 = time.perf_counter()
#        performance.update({'Conventional Dispatch': t2-t1})
#    # Capacities
#
#        query = session.query(
#            ormclass_result_gen.generator_id,
#            ormclass_result_gen.p_nom,
#            ormclass_result_gen.p_nom_opt,
#            ormclass_source.name,
#            ormclass_aggr_w.c.w_id
#        ).join(
#            ormclass_source,
#            ormclass_source.source_id == ormclass_result_gen.source
#        ).join(
#            ormclass_aggr_w,
#            ormclass_aggr_w.c.aggr_id == ormclass_result_gen.generator_id
#
#        ).filter(
#            ormclass_result_gen.bus == bus_id,
#            ormclass_result_gen.result_id == result_id,
#            ormclass_source.name.in_(weather_dpdnt),
#            ormclass_aggr_w.c.scn_name == scn_name)
#
#        ren_df = pd.DataFrame(query.all(),
#                              columns=[column['name'] for
#                                       column in
#                                       query.column_descriptions])
#
#        aggr_gens = ren_df.groupby([
#            'name',
#            'w_id'
#        ]).agg({'p_nom': 'sum'}).reset_index()
#
#        aggr_gens.rename(columns={'p_nom': 'p_nom_aggr'}, inplace=True)
#
#        aggr_gens['ren_id'] = aggr_gens.index
#
#    ### Dispatch and Curteilment
#
#        query = session.query(
#            # This is an aggregated generator ID (see ego_dp_powerflow_assignment_generator for info)
#            ormclass_result_gen_t.generator_id,
#            ormclass_result_gen_t.p,
#            # The maximum output for each snapshot per unit of p_nom for the OPF (e.g. for variable renewable generators this can change due to weather conditions; for conventional generators it represents a maximum dispatch)
#            ormclass_result_gen_t.p_max_pu
#        ).filter(
#            ormclass_result_gen_t.generator_id.in_(ren_df['generator_id']),
#            ormclass_result_gen_t.result_id == result_id
#        )
#
#        ren_t_df = pd.DataFrame(query.all(),
#                                columns=[column['name'] for
#                                         column in
#                                         query.column_descriptions])
#        ren_t_df = pd.merge(ren_t_df, ren_df, on='generator_id')[[
#            'generator_id',
#            'w_id',
#            'name',
#            'p',
#            'p_max_pu']]
#
#        dispatch = pd.DataFrame(0.0,
#                                index=snap_idx,
#                                columns=aggr_gens['ren_id'])
#        curtailment = pd.DataFrame(0.0,
#                                   index=snap_idx,
#                                   columns=aggr_gens['ren_id'])
#
#        for index, row in ren_t_df.iterrows():
#            gen_id = row['generator_id']
#            name = row['name']
#            w_id = row['w_id']
#            ren_id = int(aggr_gens[
#                (aggr_gens['name'] == name) &
#                (aggr_gens['w_id'] == w_id)]['ren_id'])
#
#            p_nom_aggr = float(
#                aggr_gens[aggr_gens['ren_id'] == ren_id]['p_nom_aggr'])
#            p_nom = float(ren_df[ren_df['generator_id'] == gen_id]['p_nom'])
#
#            p_series = pd.Series(data=row['p'], index=snap_idx)
#            p_norm_tot_series = p_series / p_nom_aggr
#
#            p_max_pu_series = pd.Series(data=row['p_max_pu'], index=snap_idx)
#            p_max_norm_tot_series = p_max_pu_series * p_nom / p_nom_aggr
#
#            p_curt_norm_tot_series = p_max_norm_tot_series - p_norm_tot_series
#
#            dispatch[ren_id] = dispatch[ren_id] + p_norm_tot_series
#            curtailment[ren_id] = curtailment[ren_id] + p_curt_norm_tot_series
#
#    except:
#        logger.exception("Generators could not be queried for \
#                         Specs with Metadata: \n %s" % specs_meta_data)
#
#    # Load
#        # Load are not part of the Specs anymore
#
#    # Storage
#    t3 = time.perf_counter()
#    performance.update({'Renewable Dispatch and Curt.': t3-t2})
#    try:
#        # Capactiy
#        query = session.query(
#            ormclass_result_stor.storage_id,
#            ormclass_result_stor.p_nom_opt,
#            ormclass_result_stor.p_nom,
#            ormclass_result_stor.max_hours,
#            ormclass_source.name
#        ).join(
#            ormclass_source,
#            ormclass_source.source_id == ormclass_result_stor.source
#        ).filter(
#            ormclass_result_stor.bus == bus_id,
#            ormclass_result_stor.result_id == result_id,
#            ormclass_source.name == 'extendable_storage')
#
#        stor_df = pd.DataFrame(query.all(),
#                               columns=[column['name'] for
#                                        column in
#                                        query.column_descriptions])
#
#        stor_df['capacity_MWh'] = stor_df['p_nom_opt'] * stor_df['max_hours']
#
#        count_bat = 0
#        for index, row in stor_df.iterrows():
#            if row['max_hours'] >= 20.0:
#                stor_df.at[index, 'name'] = 'ext_long_term'
#            else:
#                # ToDo: find a more generic solution
#                stor_df.at[index, 'name'] = 'battery'
#                count_bat += 1
#
#    # Project Specific Battery Capacity
#        battery_capacity = 0.0  # MWh
#        for index, row in stor_df.iterrows():
#            if row['name'] == 'battery':
#                battery_capacity = battery_capacity + row['capacity_MWh']
#
#    # Dispatch
#        query = session.query(
#            ormclass_result_stor_t.storage_id,
#            ormclass_result_stor_t.p,
#            ormclass_result_stor_t.state_of_charge
#        ).filter(
#            ormclass_result_stor_t.storage_id.in_(
#                stor_df['storage_id']),
#            ormclass_result_stor_t.result_id == result_id
#        )
#        stor_t_df = pd.DataFrame(query.all(),
#                                 columns=[column['name'] for
#                                          column in
#                                          query.column_descriptions])
#
#        stor_t_df = pd.merge(stor_t_df, stor_df, on='storage_id')[[
#            'storage_id',
#            'name',
#            'p',
#            'state_of_charge']]
#
#    # Project Specific Battery Active Power
#        battery_active_power = pd.Series(0.0, index=snap_idx)
#        for index, row in stor_t_df.iterrows():
#            name = row['name']
#            if name == 'battery':
#                stor_series = pd.Series(
#                    data=row['p'],  # in MW
#                    index=snap_idx)
#                stor_series_kW = [x * 1000 for x in stor_series]  # in kW
#                battery_active_power = battery_active_power + stor_series_kW
#
#    except:
#        logger.exception("Storage could not be queried for \
#                         Specs with Metadata: \n %s" % specs_meta_data)
#
#    # Return Specs
#    t4 = time.perf_counter()
#    performance.update({'Storage Data Processing and Dispatch': t4-t3})
#
#    specs = ETraGoSpecs(battery_capacity=battery_capacity,
#                        battery_active_power=battery_active_power,
#
#                        conv_dispatch=conv_dsptch_norm,
#
#                        renewables=aggr_gens,
#                        ren_dispatch=dispatch,
#                        ren_curtailment=curtailment)
#
#    # logger.info(specs_meta_data)
#    t5 = time.perf_counter()
#    performance.update({'Overall time': t5-t0})
#
# print("\n Conventional Dispatch (Normalized): \n",
# conv_dsptch_norm,
##      "\n\n Renewable Generators: \n",
# aggr_gens,
##      "\n\n Renewable Dispatch: \n",
# dispatch,
##      "\n\n Renewable Curtailment: \n",
# curtailment, "\n\n")
#
#    for keys, values in performance.items():
#        print(keys, ": ", values)
#
#    return specs


def get_etragospecs_direct(session,
                           bus_id,
                           etrago_network,
                           scn_name,
                           pf_post_lopf):
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

#    ormclass_result_meta = model_draft.__getattribute__('EgoGridPfHvResultMeta')
    ormclass_gen_single = model_draft.__getattribute__(
        'EgoSupplyPfGeneratorSingle')
#    ormclass_aggr_w = model_draft.t_ego_supply_aggr_weather_mview

#    __getattribute__(
#        'ego_supply_aggr_weather_mview')
    logger.warning('Weather table taken from model_draft')
#    ormclass_source = model_draft.__getattribute__('EgoGridPfHvSource')
#    logger.warning('Source table taken from model_draft')

    snap_idx = etrago_network.snapshots

#    # If the results are beeing recovered, the scn_name cannot be used from Scenario Settings File
#    if args['global']['recover'] == True:
#        result_id = args['global']['result_id']
#        scn_name = session.query(
#            ormclass_result_meta.scn_name
#        ).filter(
#            ormclass_result_meta.result_id == result_id
#        ).scalar(
#        )
#    else:
#        scn_name = args['eTraGo']['scn_name']
#    specs_meta_data.update({'scn_name': scn_name})
#
#    if scn_name == 'SH Status Quo':
#        scn_name = 'Status Quo'

    # Generators
    t0 = time.perf_counter()

    weather_dpdnt = ['wind', 'solar', 'wind_onshore', 'wind_offshore']

    # DF procesing
    all_gens_df = etrago_network.generators[
        etrago_network.generators['bus'] == str(bus_id)
    ]
    idx_name = all_gens_df.index.name
    
    all_gens_df.reset_index(inplace=True)

    all_gens_df = all_gens_df.rename(columns={idx_name: 'generator_id'})
   
    all_gens_df = all_gens_df[[
        'generator_id',
        'p_nom',
        'p_nom_opt',
        'carrier']]

    all_gens_df = all_gens_df.rename(columns={"carrier": "name"})

    all_gens_df = all_gens_df[all_gens_df['name'] != 'wind_offshore']
    logger.warning('Wind offshore is disregarded in the interface')

    for index, row in all_gens_df.iterrows():
        name = row['name']
        if name == 'wind_onshore':
            all_gens_df.at[index, 'name'] = 'wind'
            logger.warning('wind onshore is renamed to wind')


#    print(all_gens_df)
#    names = []
#    for index, row in all_gens_df.iterrows():
#        carrier = row['carrier']
#        name = session.query(
#            ormclass_source.name
#        ).filter(
#            ormclass_source.source_id == carrier
#        ).scalar(
#        )
#
#        names.append(name)

#    all_gens_df['name'] = names

#    all_gens_df = all_gens_df.drop(['carrier'], axis=1)
            

    # Conventionals
    t1 = time.perf_counter()
    performance.update({'Generator Data Processing': t1-t0})

    conv_df = all_gens_df[~all_gens_df.name.isin(weather_dpdnt)]

    conv_cap = conv_df[['p_nom', 'name']].groupby('name').sum().T

    conv_dsptch = pd.DataFrame(0.0,
                                    index=snap_idx,
                                    columns=list(set(conv_df['name'])))
    conv_reactive_power = pd.DataFrame(0.0,
                                    index=snap_idx,
                                    columns=list(set(conv_df['name'])))
#    conv_dsptch_abs = pd.DataFrame(0.0,
#                                   index=snap_idx,
#                                   columns=list(set(conv_df['name'])))

    for index, row in conv_df.iterrows():
        generator_id = row['generator_id']
        source = row['name']
        p = etrago_network.generators_t.p[str(generator_id)]
        p_norm = p / conv_cap[source]['p_nom']
        conv_dsptch[source] = conv_dsptch[source] + p_norm
#        conv_dsptch_abs[source] = conv_dsptch_abs[source] + p
        if pf_post_lopf:
            q = etrago_network.generators_t.q[str(generator_id)]
            q_norm = q / conv_cap[source]['p_nom'] # q normalized with p_nom
            conv_reactive_power[source] = (
                    conv_reactive_power[source] 
                    + q_norm            )

    if pf_post_lopf:
        new_columns = [
                (col, '') for col in conv_reactive_power.columns
                ]
        conv_reactive_power.columns = pd.MultiIndex.from_tuples(new_columns)
        
    
    # Renewables
    t2 = time.perf_counter()
    performance.update({'Conventional Dispatch': t2-t1})
    # Capacities
    ren_df = all_gens_df[all_gens_df.name.isin(weather_dpdnt)]

#    w_ids = []
    for index, row in ren_df.iterrows():
        aggr_id = row['generator_id']
        w_id = session.query(
            ormclass_gen_single.w_id
        ).filter(
            ormclass_gen_single.aggr_id == aggr_id,
            ormclass_gen_single.scn_name == scn_name
        ).limit(1).scalar(
        )

        ren_df.at[index, 'w_id'] = w_id

#        w_ids.append(w_id)

#    ren_df = ren_df.assign(w_id=pd.Series(w_ids, index=ren_df.index))
#    # This should be unnecessary (and I think it isnt)
    ren_df.dropna(inplace=True)
#    print(ren_df)

    aggr_gens = ren_df.groupby([
        'name',
        'w_id'
    ]).agg({'p_nom': 'sum'}).reset_index()

    aggr_gens.rename(columns={'p_nom': 'p_nom_aggr'}, inplace=True)

    aggr_gens['ren_id'] = aggr_gens.index

#    print(aggr_gens)

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

#    potential_abs = pd.DataFrame(0.0,
#                               index=snap_idx,
#                               columns=aggr_gens['ren_id'])
#    dispatch_abs = pd.DataFrame(0.0,
#                               index=snap_idx,
#                               columns=aggr_gens['ren_id'])
#    curtailment_abs = pd.DataFrame(0.0,
#                               index=snap_idx,
#                               columns=aggr_gens['ren_id'])

    for index, row in ren_df.iterrows():
        gen_id = row['generator_id']
        name = row['name']
        w_id = row['w_id']
        ren_id = int(aggr_gens[
            (aggr_gens['name'] == name) &
            (aggr_gens['w_id'] == w_id)]['ren_id'])

        p_nom_aggr = float(
            aggr_gens[aggr_gens['ren_id'] == ren_id]['p_nom_aggr'])
#        p_nom = float(ren_df[ren_df['generator_id'] == gen_id]['p_nom'])
        p_nom = row['p_nom']

        p_series = etrago_network.generators_t.p[str(gen_id)]
        p_norm_tot_series = p_series / p_nom_aggr

        p_max_pu_series = etrago_network.generators_t.p_max_pu[str(gen_id)]
#        p_max_series = p_max_pu_series * p_nom
        p_max_norm_tot_series = p_max_pu_series * p_nom / p_nom_aggr

#        p_curt_tot_series = p_max_series - p_series
#        p_curt_norm_tot_series = p_max_norm_tot_series - p_norm_tot_series

        potential[ren_id] = potential[ren_id] + p_max_norm_tot_series
        dispatch[ren_id] = dispatch[ren_id] + p_norm_tot_series
#        curtailment[ren_id] = curtailment[ren_id] + p_curt_norm_tot_series
        
        if pf_post_lopf:
            q_series = etrago_network.generators_t.q[str(gen_id)] 
            q_norm_tot_series = q_series / p_nom_aggr
            reactive_power[ren_id] = (
                    reactive_power[ren_id] 
                    + q_norm_tot_series)
            
#    potential = potential.round(3)
#    dispatch = dispatch.round(3)
#
#    logger.warning('Rounding normalized values')
    curtailment = potential.sub(dispatch)


#        potential_abs[ren_id] = potential_abs[ren_id] + p_max_series
#        dispatch_abs[ren_id] = dispatch_abs[ren_id] + p_series
#        curtailment_abs[ren_id] = curtailment_abs[ren_id] + p_curt_tot_series


#    potential = dispatch + curtailment

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
        
        ### Reactive Power concat
        all_reactive_power = pd.concat([
                conv_reactive_power, 
                reactive_power], axis=1)
        

#    new_columns = [
#        (aggr_gens[aggr_gens.ren_id == col].name.iloc[0],
#         aggr_gens[aggr_gens.ren_id == col].w_id.iloc[0])
#        for col in potential_abs.columns]
#    potential_abs.columns = pd.MultiIndex.from_tuples(new_columns)
#
#    new_columns = [
#        (aggr_gens[aggr_gens.ren_id == col].name.iloc[0],
#         aggr_gens[aggr_gens.ren_id == col].w_id.iloc[0])
#        for col in dispatch_abs.columns]
#    dispatch_abs.columns = pd.MultiIndex.from_tuples(new_columns)
#
#    new_columns = [
#        (aggr_gens[aggr_gens.ren_id == col].name.iloc[0],
#         aggr_gens[aggr_gens.ren_id == col].w_id.iloc[0])
#        for col in curtailment_abs.columns]
#    curtailment_abs.columns = pd.MultiIndex.from_tuples(new_columns)
#
#    potential_abs = potential_abs * 1000 # Absolute amounts in kW
#    dispatch_abs = dispatch_abs * 1000
#    curtailment_abs = curtailment_abs * 1000
        
    

    # Storage
    t3 = time.perf_counter()
    performance.update({'Renewable Dispatch and Curt.': t3-t2})
    # Capactiy
    stor_df = etrago_network.storage_units.loc[
        (etrago_network.storage_units['bus'] == str(bus_id))
        & (etrago_network.storage_units['p_nom_extendable'] == True)
        & (etrago_network.storage_units['p_nom_opt'] > 0.)
        & (etrago_network.storage_units['max_hours'] <= 20.)]  # Only batteries

    ext_found = False
    if len(stor_df) == 1:
        logger.info('Extendable storage unit found')
        ext_found = True

        stor_id = stor_df.index[0]
#        p_nom_opt = stor_df['p_nom_opt'].values[0]

    #    stor_df.reset_index(inplace=True)
    #    stor_df = stor_df.rename(columns={'index': 'storage_id'})
    #        stor_df = stor_df[[
    #            'p_nom_opt',
    #            'p_nom']]


#    names = []
#    for index, row in stor_df.iterrows():
#        carrier = row['carrier']
#        name = session.query(
#            ormclass_source.name
#        ).filter(
#            ormclass_source.source_id == carrier
#        ).scalar(
#        )
#
#        names.append(name)
#
#    stor_df = stor_df.assign(name=pd.Series(names, index=stor_df.index))
#    stor_df = stor_df.drop(['carrier'], axis=1)

#    stor_df = stor_df.rename(columns={"carrier": "name"})

#    stor_df['capacity_MWh'] = stor_df['p_nom_opt'] * stor_df['max_hours']

#    count_bat = 0
#    for index, row in stor_df.iterrows():
#        if row['max_hours'] >= 20.0:
#            stor_df.at[index, 'name'] = 'ext_long_term'
#        else:
#            # ToDo: find a more generic solution
#            stor_df.at[index, 'name'] = 'battery'
#            count_bat += 1

# Project Specific Battery Capacity
#    battery_capacity = 0.0  # MWh
#    for index, row in stor_df.iterrows():
#        if row['name'] == 'battery':
#            battery_capacity = battery_capacity + row['capacity_MWh']

 # Project Specific Battery Active Power
#    battery_active_power = pd.Series(0.0, index=snap_idx)
#    for index, row in stor_df.iterrows():
#        name = row['name']
#        stor_id = row['storage_id']
#        if name == 'battery':
#            stor_series = etrago_network.storage_units_t.p[str(stor_id)]
#            stor_series_kW = stor_series * 1000
#            battery_active_power = battery_active_power + stor_series_kW

        stor_p_series_kW = etrago_network.storage_units_t.p[

                str(stor_id)] * 1000
          
        if pf_post_lopf:
            stor_q_series_kvar = etrago_network.storage_units_t.q[
                    str(stor_id)] * 1000
    
    t4 = time.perf_counter()
    performance.update({'Storage Data Processing and Dispatch': t4-t3})

    specs = {
#        'battery_capacity': battery_capacity,
#        'battery_p_series': stor_p_series_kW ,
        'conv_dispatch': conv_dsptch,
        #            'conv_dispatch_abs': conv_dsptch_abs,
        #            'renewables': aggr_gens,
        'ren_dispatch': dispatch,
        #            'dispatch_abs': dispatch_abs,
        'ren_potential': potential,
        #            'potential_abs': potential_abs,
        'ren_curtailment': curtailment  # ,
        #            'curtailment_abs': curtailment_abs
    }

    if ext_found:
        specs['battery_p_series'] = stor_p_series_kW

        if pf_post_lopf:
            specs['battery_q_series'] = stor_q_series_kvar

#    print(specs['battery_p_series'])
#    specs = ETraGoSpecs(battery_capacity=battery_capacity,
#                        battery_active_power=battery_active_power,
#
#                        conv_dispatch=conv_dsptch_norm,
#
#                        renewables=aggr_gens,
#                        ren_dispatch=dispatch,
#                        ren_curtailment=curtailment)
    test = True
    if test == True:
        print('\nConventional capacity: \n')
        print(conv_cap)
        print('\nConventional dispatch: \n')
        print(conv_dsptch)
        
        print('\nRenewable capacity: \n')
        print(aggr_gens)
        print('\nRenewable Potential: \n')
        print(potential)
        
        if pf_post_lopf:
            print('\nReactive Power: \n')
            print(all_reactive_power)
        

    if pf_post_lopf:
        specs['reactive_power'] = all_reactive_power
        
        
        
    t5 = time.perf_counter()
    performance.update({'Overall time': t5-t0})

#    for keys,values in performance.items():
#        print(keys, ": ", values)

    return specs
