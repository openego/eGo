# Import
## General Packages
import os
import pandas as pd
if not 'READTHEDOCS' in os.environ:
    from sqlalchemy import distinct
    from egoio.db_tables import model_draft # This gives me the specific ORM classes.
    from edisgo.grid.network import ETraGoSpecs

import logging # ToDo: Logger should be set up more specific
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#############################
# ToDo: Alquemy Hack - Put into IO
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ARRAY, BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, Numeric, SmallInteger, String, Table, Text, UniqueConstraint, text

Base = declarative_base()
metadata = Base.metadata

class EgoSupplyAggrWeather(Base):
    __tablename__ = 'ego_supply_aggr_weather'
    __table_args__ = {'schema': 'model_draft'}

    idx = Column(Integer, primary_key=True)
    w_id = Column(BigInteger)
    aggr_id = Column(BigInteger)
    scn_name = Column(String)
    bus = Column(BigInteger)
###############################  

# Functions

def get_etragospecs_from_db(session,
                            bus_id,
                            result_id):
    """
    Reads eTraGo Results from Database and returns an Object of the Interface class ETraGoSpecs

    Parameters
    ----------
    session : :class:`~.` #Todo: Add class etc....
        Oemof session object (Database Interface)
    bus_id : int
        ID of the corresponding HV bus
    result_id : int
        ID of the corresponding database result


    Returns
    -------
    etragospecs : :class:~.`
        eDisGo ETraGoSpecs Object

    """

    specs_meta_data = {}

    specs_meta_data.update({'TG Bus ID':bus_id})
    specs_meta_data.update({'Result ID':result_id})


    # Mapping
    ormclass_result_meta = model_draft.__getattribute__('EgoGridPfHvResultMeta')
    ormclass_result_bus = model_draft.__getattribute__('EgoGridPfHvResultBus') # Instead of using the automapper, this is the explicit alternative (from egoei.db_tables).
    #ormclass_result_bus = model_draft.EgoGridPfHvResultBus # This is equivalent
    #ormclass_result_bus_t = model_draft.__getattribute__('EgoGridPfHvResultBusT')
    ormclass_result_gen = model_draft.__getattribute__('EgoGridPfHvResultGenerator')
    ormclass_result_gen_t = model_draft.__getattribute__('EgoGridPfHvResultGeneratorT')
    ormclass_result_gen_single = model_draft.__getattribute__('EgoSupplyPfGeneratorSingle')
    #ormclass_result_load = model_draft.__getattribute__('EgoGridPfHvResultLoad')
    #ormclass_result_load_t = model_draft.__getattribute__('EgoGridPfHvResultLoadT')
    ormclass_result_stor = model_draft.__getattribute__('EgoGridPfHvResultStorage')
    ormclass_result_stor_t = model_draft.__getattribute__('EgoGridPfHvResultStorageT')
    ormclass_source = model_draft.__getattribute__('EgoGridPfHvSource')
    #ormclass_aggr_w = model_draft.__getattribute__('EgoSupplyAggrWeather')
    ormclass_aggr_w = EgoSupplyAggrWeather # ToDo: Noch in model_draft einführen.
    
    # Meta Queries
    ## Check

    if session.query(ormclass_result_bus).filter(
            ormclass_result_bus.bus_id == bus_id,
            ormclass_result_bus.result_id == result_id
            ).count() == 0:
        logger.warning('Bus not found')

    ## Snapshot Range

    snap_idx = session.query(
            ormclass_result_meta.snapshots
            ).filter(
            ormclass_result_meta.result_id == result_id
            ).scalar(
                    )

    scn_name = session.query(
            ormclass_result_meta.scn_name
            ).filter(
            ormclass_result_meta.result_id == result_id
            ).scalar(
                    )


    specs_meta_data.update({'scn_name':scn_name})

    # Generators
    try:
        weather_dpdnt = ['wind','solar']
    ## Conventionals
        query = session.query(
                ormclass_result_gen.generator_id, # This ID is an aggregate ID (single generators aggregated)
                ormclass_result_gen.p_nom,
                ormclass_source.name
                ).join(
                        ormclass_source,
                        ormclass_source.source_id == ormclass_result_gen.source
                        ).filter(
                                ormclass_result_gen.bus == bus_id,
                                ormclass_result_gen.result_id == result_id,
                                ormclass_source.name.notin_(weather_dpdnt))

        conv_df = pd.DataFrame(query.all(),
                              columns=[column['name'] for
                                       column in
                                       query.column_descriptions])

        conv_cap = conv_df[['p_nom','name']].groupby('name').sum().T

        query = session.query(
                    ormclass_result_gen_t.generator_id,
                    ormclass_result_gen_t.p
                    ).filter(
                    ormclass_result_gen_t.generator_id.in_(conv_df['generator_id']),
                    ormclass_result_gen_t.result_id == result_id
                    )

        conv_t_df = pd.DataFrame(query.all(),
                                    columns=[column['name'] for column in query.column_descriptions])

        conv_t_df = pd.merge(conv_df,
                               conv_t_df,
                               on='generator_id')[[
                             'name',
                             'p']]

        conv_dsptch_norm = pd.DataFrame(0.0,
                                   index=snap_idx,
                                   columns=list(set(conv_df['name'])))

        for index, row in conv_t_df.iterrows():
                source = row['name']
                gen_series_norm = pd.Series(
                        data=(row['p'] / conv_cap[source]['p_nom'] ), # Every generator normalized by installed capacity.
                        index=snap_idx)
                conv_dsptch_norm[source] = conv_dsptch_norm[source] + gen_series_norm

    ## Renewables
    ### Capacities
         
        query = session.query(
                ormclass_result_gen.generator_id,
                ormclass_result_gen.p_nom,
                ormclass_result_gen.p_nom_opt,
                ormclass_source.name,
                ormclass_aggr_w.w_id
                ).join(
                        ormclass_source,
                        ormclass_source.source_id == ormclass_result_gen.source
                                ).join(
                                        ormclass_aggr_w,
                                        ormclass_aggr_w.aggr_id == ormclass_result_gen.generator_id
                                        
                                ).filter(
                                ormclass_result_gen.bus == bus_id,
                                ormclass_result_gen.result_id == result_id,
                                ormclass_source.name.in_(weather_dpdnt),
                                ormclass_aggr_w.scn_name == scn_name)
        
        ren_df = pd.DataFrame(query.all(),
                              columns=[column['name'] for
                                       column in
                                       query.column_descriptions])
    # ToDo: apparently gens come form different scn Names here!!! Check single table!!!!!
    # At least this is the case with result_id 9!!!!

        aggr_gens = ren_df.groupby([
                'name',
                'w_id'
                ]).agg({'p_nom': 'sum'}).reset_index()

        aggr_gens.rename(columns={'p_nom': 'p_nom_aggr'}, inplace=True)

        aggr_gens['ren_id'] = aggr_gens.index

    ### Dispatch and Curteilment

        query = session.query(
                ormclass_result_gen_t.generator_id, # This is an aggregated generator ID (see ego_dp_powerflow_assignment_generator for info)
                ormclass_result_gen_t.p,
                ormclass_result_gen_t.p_max_pu # The maximum output for each snapshot per unit of p_nom for the OPF (e.g. for variable renewable generators this can change due to weather conditions; for conventional generators it represents a maximum dispatch)
                ).filter(
                ormclass_result_gen_t.generator_id.in_(ren_df['generator_id']),
                ormclass_result_gen_t.result_id == result_id
                )

        ren_t_df = pd.DataFrame(query.all(),
                                columns=[column['name'] for
                                         column in
                                         query.column_descriptions])
        ren_t_df = pd.merge(ren_t_df, ren_df, on='generator_id')[[
                'generator_id',
                'w_id',
                'name',
                'p',
                'p_max_pu']]

        dispatch = pd.DataFrame(0.0,
                                index=snap_idx,
                                columns=aggr_gens['ren_id'])
        curtailment = pd.DataFrame(0.0,
                                index=snap_idx,
                                columns=aggr_gens['ren_id'])

        for index, row in ren_t_df.iterrows():
            gen_id = row['generator_id']
            name = row['name']
            w_id = row['w_id']
            ren_id = int(aggr_gens[
                    (aggr_gens['name'] == name) &
                    (aggr_gens['w_id'] == w_id)]['ren_id'])

            p_nom_aggr = float(aggr_gens[aggr_gens['ren_id'] == ren_id]['p_nom_aggr'])
            p_nom = float(ren_df[ren_df['generator_id'] == gen_id]['p_nom'])


            p_series = pd.Series(data=row['p'], index=snap_idx)
            p_norm_tot_series = p_series / p_nom_aggr

            p_max_pu_series = pd.Series(data=row['p_max_pu'], index=snap_idx)
            p_max_norm_tot_series = p_max_pu_series * p_nom / p_nom_aggr

            p_curt_norm_tot_series = p_max_norm_tot_series - p_norm_tot_series


            dispatch[ren_id] = dispatch[ren_id] + p_norm_tot_series
            curtailment[ren_id] = curtailment[ren_id] + p_curt_norm_tot_series

    except:
        logger.exception("Generators could not be queried for \
                         Specs with Metadata: \n %s" %specs_meta_data)

    # Load
        # Load are not part of the Specs anymore

    # Storage
    try:
    ## Capactiy
        query = session.query(
                ormclass_result_stor.storage_id,
                ormclass_result_stor.p_nom_opt,
                ormclass_result_stor.p_nom,
                ormclass_result_stor.max_hours,
                ormclass_source.name
                ).join(
                        ormclass_source,
                        ormclass_source.source_id == ormclass_result_stor.source
                        ).filter(
                                ormclass_result_stor.bus == bus_id,
                                ormclass_result_stor.result_id == result_id,
                                ormclass_source.name == 'extendable_storage')

        stor_df = pd.DataFrame(query.all(),
                              columns=[column['name'] for
                                       column in
                                       query.column_descriptions])


        stor_df['capacity_MWh'] = stor_df['p_nom_opt'] * stor_df['max_hours']

        count_bat = 0
        for index, row in stor_df.iterrows():
            if row['max_hours'] >= 20.0:
                stor_df.at[index, 'name'] = 'ext_long_term'
            else:
                stor_df.at[index, 'name'] = 'battery' # ToDo: find a more generic solution
                count_bat += 1

    ### Project Specific Battery Capacity
        battery_capacity = 0.0 # MWh
        for index, row in stor_df.iterrows():
            if row['name'] == 'battery':
                battery_capacity = battery_capacity + row['capacity_MWh']

    ## Dispatch
        query = session.query(
                    ormclass_result_stor_t.storage_id,
                    ormclass_result_stor_t.p,
                    ormclass_result_stor_t.state_of_charge
                    ).filter(
                                ormclass_result_stor_t.storage_id.in_(
                                        stor_df['storage_id']),
                                ormclass_result_stor_t.result_id == result_id
                    )
        stor_t_df = pd.DataFrame(query.all(),
                                    columns=[column['name'] for
                                             column in
                                             query.column_descriptions])

        stor_t_df = pd.merge(stor_t_df, stor_df, on='storage_id')[[
                'storage_id',
                'name',
                'p',
                'state_of_charge']]

    ### Project Specific Battery Active Power
        battery_active_power = pd.Series(0.0, index = snap_idx)
        for index, row in stor_t_df.iterrows():
            name = row['name']
            if name == 'battery':
                stor_series = pd.Series(
                        data=row['p'], # in MW
                        index=snap_idx)
                stor_series_kW = [x * 1000 for x in stor_series] # in kW
                battery_active_power = battery_active_power + stor_series_kW

    except:
        logger.exception("Storage could not be queried for \
                         Specs with Metadata: \n %s" %specs_meta_data)


    # Return Specs

    specs = ETraGoSpecs(battery_capacity=battery_capacity,
                        battery_active_power=battery_active_power,

                        conv_dispatch=conv_dsptch_norm,

                        renewables=aggr_gens,
                        ren_dispatch=dispatch,
                        ren_curtailment=curtailment)

    logger.info(specs_meta_data)
    print(ren_df)
    print(aggr_gens, dispatch, curtailment)

    return specs


def get_etragospecs_direct(session,
                            bus_id,
                            result_id,
                            eTraGo,
                            args):
    """
    Reads eTraGo Results from Database and returns an Object of the Interface class ETraGoSpecs

    Parameters
    ----------
    session : :class:`~.` #Todo: Add class etc....
        Oemof session object (Database Interface)
    bus_id : int
        ID of the corresponding HV bus
    result_id : int
        ID of the corresponding database result
    eTraGo : :class:`~.` #Todo: Add class etc....    


    Returns
    -------
    etragospecs : :class:~.`
        eDisGo ETraGoSpecs Object

    """
    
    specs_meta_data = {}

    specs_meta_data.update({'TG Bus ID':bus_id})
    specs_meta_data.update({'Result ID':result_id})
   
    ormclass_aggr_w = EgoSupplyAggrWeather # Todo include truely
    ormclass_source = model_draft.__getattribute__('EgoGridPfHvSource')
    
    snap_idx =  eTraGo.snapshots
    
    scn_name = args['eTraGo']['scn_name']
    specs_meta_data.update({'scn_name':scn_name})
    
    # Generators
    weather_dpdnt = ['wind','solar']
 
    ## DF procesing
    all_gens_df = eTraGo.generators[eTraGo.generators['bus'] == str(bus_id)]
    all_gens_df.reset_index(inplace=True)
    all_gens_df.rename(columns={'index':'generator_id'}, inplace=True)
    all_gens_df = all_gens_df[['generator_id', 'p_nom', 'p_nom_opt', 'carrier']]
    
    names = []
    for index, row in all_gens_df.iterrows():  
        carrier = row['carrier']
        name = session.query(
                    ormclass_source.name
                        ).filter(
                                ormclass_source.source_id == carrier
                                ).scalar(
                                        )
        
        names.append(name)
            
    all_gens_df['name'] = names
    all_gens_df = all_gens_df.drop(['carrier'], axis=1)
    

    ## Conventionals
    conv_df = all_gens_df[~all_gens_df.name.isin(weather_dpdnt)]
    conv_cap = conv_df[['p_nom','name']].groupby('name').sum().T
    
    conv_dsptch_norm = pd.DataFrame(0.0,
                               index=snap_idx,
                               columns=list(set(conv_df['name'])))

    for index, row in conv_df.iterrows():
        generator_id = row['generator_id']
        source = row['name']
        p = eTraGo.generators_t.p[str(generator_id)]
        p_norm = p / conv_cap[source]['p_nom']
        conv_dsptch_norm[source] = conv_dsptch_norm[source] + p_norm
        
    ## Renewables
    ### Capacities
    ren_df = all_gens_df[all_gens_df.name.isin(weather_dpdnt)]
    
    w_ids = []
    for index, row in ren_df.iterrows():  
        aggr_id = row['generator_id']
        w_id = session.query(
                    ormclass_aggr_w.w_id
                        ).filter(
                                ormclass_aggr_w.aggr_id == aggr_id,
                                ormclass_aggr_w.scn_name == scn_name 
                                ).scalar(
                                        )
        
        w_ids.append(w_id)
            
    ren_df['w_id'] = w_ids   
    ren_df.dropna(inplace=True) ##This should be unnecessary
    
    aggr_gens = ren_df.groupby([
            'name',
            'w_id'
            ]).agg({'p_nom': 'sum'}).reset_index()

    aggr_gens.rename(columns={'p_nom': 'p_nom_aggr'}, inplace=True)

    aggr_gens['ren_id'] = aggr_gens.index

    ### Dispatch and Curteilment
    dispatch = pd.DataFrame(0.0,
                            index=snap_idx,
                            columns=aggr_gens['ren_id'])
    curtailment = pd.DataFrame(0.0,
                            index=snap_idx,
                            columns=aggr_gens['ren_id'])        

    for index, row in ren_df.iterrows():
        gen_id = row['generator_id']
        name = row['name']
        w_id = row['w_id']
        ren_id = int(aggr_gens[
                (aggr_gens['name'] == name) &
                (aggr_gens['w_id'] == w_id)]['ren_id'])

        p_nom_aggr = float(aggr_gens[aggr_gens['ren_id'] == ren_id]['p_nom_aggr'])
        p_nom = float(ren_df[ren_df['generator_id'] == gen_id]['p_nom'])
        
        p_series = eTraGo.generators_t.p[str(gen_id)]
        p_norm_tot_series = p_series / p_nom_aggr

        p_max_pu_series = eTraGo.generators_t.p_max_pu[str(gen_id)]
        p_max_norm_tot_series = p_max_pu_series * p_nom / p_nom_aggr
    
        p_curt_norm_tot_series = p_max_norm_tot_series - p_norm_tot_series
        
        dispatch[ren_id] = dispatch[ren_id] + p_norm_tot_series
        curtailment[ren_id] = curtailment[ren_id] + p_curt_norm_tot_series
 
    # Storage
    ## Capactiy
    stor_df = eTraGo.storage_units[eTraGo.storage_units['bus'] == str(bus_id)]
    stor_df.reset_index(inplace=True)
    stor_df.rename(columns={'index':'storage_id'}, inplace=True)
    stor_df = stor_df[[
            'storage_id', 
            'p_nom_opt', 
            'p_nom',
            'max_hours',
            'carrier']]
    
    names = []
    for index, row in stor_df.iterrows():  
        carrier = row['carrier']
        name = session.query(
                    ormclass_source.name
                        ).filter(
                                ormclass_source.source_id == carrier
                                ).scalar(
                                        )
        
        names.append(name)
            
    stor_df['name'] = names
    stor_df = stor_df.drop(['carrier'], axis=1)
    
    stor_df['capacity_MWh'] = stor_df['p_nom_opt'] * stor_df['max_hours']
       
    count_bat = 0
    for index, row in stor_df.iterrows():
        if row['max_hours'] >= 20.0:
            stor_df.at[index, 'name'] = 'ext_long_term'
        else:
            stor_df.at[index, 'name'] = 'battery' # ToDo: find a more generic solution
            count_bat += 1
    
### Project Specific Battery Capacity
    battery_capacity = 0.0 # MWh
    for index, row in stor_df.iterrows():
        if row['name'] == 'battery':
            battery_capacity = battery_capacity + row['capacity_MWh']

 ### Project Specific Battery Active Power
    battery_active_power = pd.Series(0.0, index = snap_idx)       
    for index, row in stor_df.iterrows():
        name = row['name']
        stor_id = row['storage_id']
        if name == 'battery':
            stor_series = eTraGo.storage_units_t.p[str(stor_id)]
            stor_series_kW = stor_series * 1000
            battery_active_power = battery_active_power + stor_series_kW

    specs = ETraGoSpecs(battery_capacity=battery_capacity,
                        battery_active_power=battery_active_power,

                        conv_dispatch=conv_dsptch_norm,

                        renewables=aggr_gens,
                        ren_dispatch=dispatch,
                        ren_curtailment=curtailment) 
    
    print(ren_df)
    print(aggr_gens, dispatch, curtailment)
    
    
    return specs


def get_mvgrid_from_bus_id(session,
                            bus_id):    
    # Mapping
    ormclass_hvmv_subst = model_draft.__getattribute__('EgoGridHvmvSubstation')
    subst_id = session.query(
            ormclass_hvmv_subst.subst_id
            ).filter(
            ormclass_hvmv_subst.otg_id == bus_id
            ).scalar(
                    )
    #ToDo Check if subst_id is really the mv grid ID
    # Anyway, this should be adapted by Dingo
    return subst_id
 
   