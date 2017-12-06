# Import
## General Packages
    
import pandas as pd    
import numpy as np
import logging # ToDo: Logger should be set up more specific
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## Project Packages
    
from egoio.db_tables import model_draft # This gives me the specific ORM classes.
from edisgo.grid.network import ETraGoSpecs 

def get_etragospecs_from_db(session, 
                            bus_id, 
                            result_id=1):
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
    ormclass_result_bus_t = model_draft.__getattribute__('EgoGridPfHvResultBusT')
    ormclass_result_gen = model_draft.__getattribute__('EgoGridPfHvResultGenerator')
    ormclass_result_gen_t = model_draft.__getattribute__('EgoGridPfHvResultGeneratorT')
    ormclass_result_load = model_draft.__getattribute__('EgoGridPfHvResultLoad')
    ormclass_result_load_t = model_draft.__getattribute__('EgoGridPfHvResultLoadT')
    ormclass_result_stor = model_draft.__getattribute__('EgoGridPfHvResultStorage')
    ormclass_result_stor_t = model_draft.__getattribute__('EgoGridPfHvResultStorageT')
    ormclass_source = model_draft.__getattribute__('EgoGridPfHvSource')
    
# Query all Data   
## Check

    if session.query(ormclass_result_bus).filter(
            ormclass_result_bus.bus_id == bus_id,
            ormclass_result_bus.result_id == result_id
            ).count() == 0:
        logger.warning('Bus not found')
        return None
    
## Snapshot Range 
    
    snap_idx = session.query( 
            ormclass_result_meta.snapshots
            ).filter(
            ormclass_result_meta.result_id == result_id
            ).scalar(
                    )
      
## Bus Power
    query = session.query(
            ormclass_result_bus_t.p
            ).filter(
            ormclass_result_bus_t.bus_id == bus_id, 
            ormclass_result_bus_t.result_id == result_id
            ).scalar( 
                    )  
    try:
        active_power_kW = pd.Series( 
            data=(np.array(query) * 1000 ), # PyPSA result is in MW
            index=snap_idx) 
    except:
        logger.warning('No active power series')
        active_power_kW = None
        
    query = session.query(
            ormclass_result_bus_t.q
            ).filter(
            ormclass_result_bus_t.bus_id == bus_id,
            ormclass_result_bus_t.result_id == result_id
            ).scalar(
                    )
    try:
        reactive_power_kvar = pd.Series( 
            data=(np.array(query) * 1000 ), # PyPSA result is in Mvar
            index=snap_idx) 
    except:
        logger.warning('No reactive power series')
        reactive_power_kvar = None
     
## Gen Capacity
    try:
        query = session.query(
                ormclass_result_gen.generator_id,
                ormclass_result_gen.p_nom,
                ormclass_source.name
                ).join(
                        ormclass_source, 
                        ormclass_source.source_id == ormclass_result_gen.source
                        ).filter(
                                ormclass_result_gen.bus == bus_id,
                                ormclass_result_gen.result_id == result_id) 
        logger.debug("Dataframe from gens query")  
        gen_df = pd.DataFrame(query.all(), 
                              columns=[column['name'] for column in query.column_descriptions]) 
        
        capacity = gen_df[['p_nom','name']].groupby('name').sum().T
    except:
        logger.warning('No capactity calculated')
        capacity = None
        
## Gen Dispatch    
    try: 
        query = session.query(
                ormclass_result_gen_t.generator_id,
                ormclass_result_gen_t.p,
                ormclass_result_gen_t.p_max_pu
                ).filter(
                ormclass_result_gen_t.generator_id.in_(gen_df['generator_id']),
                ormclass_result_gen_t.result_id == result_id
                )     
        
        gen_t_df = pd.DataFrame(query.all(), 
                                columns=[column['name'] for column in query.column_descriptions]) 
        
        p_df = pd.merge(gen_df, gen_t_df, on='generator_id')[['name','p']]
        
        dispatch = pd.DataFrame(0.0, index=snap_idx, columns=list(set(p_df['name']))) 
        
        for index, row in p_df.iterrows():
            source = row['name']
            gen_series_norm = pd.Series(
                    data=(row['p'] / capacity[source]['p_nom'] ), # Every generator normalized by installed capacity.
                    index=snap_idx)
            
            for snap in snap_idx:
                dispatch[source][snap] = dispatch[source][snap] + gen_series_norm[snap] # Aggregatet by source (adds up)
    except:
        logger.warning('No dispatch calculated')
        dispatch = None   
        
## Curtailment
    try:
        p_pot_df = pd.merge(gen_df, 
                            gen_t_df, 
                            on='generator_id')[['name','p_nom','p_max_pu','p']].dropna(subset=['p_max_pu']) 
        
        p_pot_l = []
        for index, row in p_pot_df.iterrows():        
            val = [x * row['p_nom'] for x in row['p_max_pu']]
            p_pot_l.append(val)
        p_pot_df['p_pot'] = p_pot_l
        
        potential = pd.DataFrame(0.0, 
                                   index=snap_idx, 
                                   columns=list(set(p_pot_df['name']))) 
        
        for index, row in p_pot_df.iterrows():
            source = row['name']
            gen_series_norm = pd.Series(
                    data=(row['p_pot'] / capacity[source]['p_nom'] ), # Every generator normalized by installed capacity.
                    index=snap_idx)
            
            for snap in snap_idx:
                potential[source][snap] = potential[source][snap] + gen_series_norm[snap] # Aggregated by source (adds up)
        
        curtailment = pd.DataFrame(0.0, 
                                   index=snap_idx, 
                                   columns=list(set(p_pot_df['name'])))
    
        for column in curtailment:
            curtailment[column] = potential[column] - dispatch[column]
    except:
        logger.warning('No curtailment calculated')
        curtailment = None

## Load
    query = session.query(
            ormclass_result_load.load_id 
            ).filter(
            ormclass_result_load.bus == bus_id,
            ormclass_result_load.result_id == result_id)
    load_ids = []
    for row in query:
        load_ids.append(row.load_id)
       
    specs_meta_data.update({'Load IDs':load_ids})
    load_types = ['retail'] # ToDo: Should be retrieved directly from Database
    logger.warning('Load types are all aggregated to %s', load_types)
    all_types = ['retail', 'agricultural', 'residential', 'industrial']
    
## Annual Load
    try:
        annual_load = pd.DataFrame(0.0, index=['Annual Load'], columns=list(set(all_types)))
        
        for i, load_id in enumerate(load_ids):
            
            load_type = load_types[i]
            annual_load_MWh = session.query(
                    ormclass_result_load.e_annual
                    ).filter(
                    ormclass_result_load.load_id == load_id,
                    ormclass_result_load.result_id == result_id
                    ).scalar(
                            ) * 1000 # Annual load in GWh (As PyPSA)    
            
            annual_load[load_type]['Annual Load'] = annual_load[load_type]['Annual Load'] + annual_load_MWh
    except:
        logger.warning('No annual laod')
        annual_load = None
        
## Load series
    try:
        load = pd.DataFrame(0.0, index=snap_idx, columns=list(set(all_types)))
        
        for i, load_id in enumerate(load_ids):
            
            load_type = load_types[i]
            load_MW = session.query(
                    ormclass_result_load_t.p   
                    ).filter(
                    ormclass_result_load_t.load_id == load_id,
                    ormclass_result_load_t.result_id == result_id
                    ).scalar(
                            )
        
            load_series_norm = pd.Series(
                    data=(np.array(load_MW) / annual_load[load_type]['Annual Load'] ), # annual_laod in MW
                    index=snap_idx)
            
            for snap in snap_idx:
                load[load_type][snap] = load[load_type][snap] + load_series_norm[snap] 
    except:
        logger.warning('No load series')
        load = None
        
## Storage    
    query = session.query(
            ormclass_result_stor.storage_id # More than one storage device is possible...
            ).filter(
            ormclass_result_stor.bus == bus_id,
            ormclass_result_stor.result_id == result_id)
    stor_ids = []
    for row in query:
        stor_ids.append(row.storage_id)
       
    stor_sources = [] 
    for id in stor_ids:   
        query = session.query(ormclass_source.name
                  ).filter(
                          ormclass_source.source_id==ormclass_result_stor.source
                          ).filter(
                                  ormclass_result_stor.storage_id==id,
                                  ormclass_result_stor.result_id == result_id).scalar()
        stor_sources.append(query)
   
    specs_meta_data.update({'Storage IDs':stor_ids})
    specs_meta_data.update({'Storage Sources':stor_sources}) #Should all be extendable if short term
    
## Storage Capacity
    try:
        stor_capacity = pd.DataFrame(0.0, 
                                     index=['extendable_storage'], 
                                     columns=['short_term', 'long_term'])
        
        for i, stor_id in enumerate(stor_ids):
            
            source = stor_sources[i]
            if source == 'extendable_storage':
                p_nom_opt_MW = session.query(
                        ormclass_result_stor.p_nom_opt
                        ).filter(
                        ormclass_result_stor.storage_id == stor_id,
                        ormclass_result_stor.result_id == result_id
                        ).scalar(
                                )
            
                max_hours = session.query(
                        ormclass_result_stor.max_hours
                        ).filter(
                        ormclass_result_stor.storage_id == stor_id,
                        ormclass_result_stor.result_id == result_id
                        ).scalar(
                                )
                
                if max_hours <= 20:
                    stor_type = 'short_term'
                else:
                    stor_type = 'long_term'
    
                    
                stor_capacity[stor_type][source] = stor_capacity[stor_type][source] + p_nom_opt_MW * max_hours
        logger.warning('Only short term extendable storage is considered battery storage') #ToDo: Check if this can be improved       
        battery_capacity = stor_capacity['short_term']['extendable_storage']
    except:
        logger.warning('No storage capacity calculated')
        battery_capacity = None
            
## Storage Active Power
    try:
        stor_active_power = pd.DataFrame(0.0, 
                                            index=snap_idx, 
                                            columns=list(set(stor_sources)))
        
        for i, stor_id in enumerate(stor_ids):
            
            source = stor_sources[i]
            query = session.query(
                    ormclass_result_stor_t.p
                    ).filter(
                    ormclass_result_stor_t.storage_id == stor_id,
                    ormclass_result_stor_t.result_id == result_id
                    ).scalar(
                            )
            stor_active_power_series_kW = pd.Series( 
                data=(np.array(query) * 1000 ), # PyPSA result is in MW
                index=snap_idx)
        
            for snap in snap_idx:
                stor_active_power[source][snap] = stor_active_power[source][snap] + stor_active_power_series_kW[snap] # Aggregatet by source (adds up) 
            
        battery_active_power = stor_active_power['extendable_storage']
    except:
        logger.warning('No storage timeseries detected')
        battery_active_power = None        
    
# Return Specs
    
    specs = ETraGoSpecs(active_power=active_power_kW,
                        reactive_power=reactive_power_kvar,
                        battery_capacity=battery_capacity,
                        battery_active_power=battery_active_power,
                        dispatch=dispatch,
                        capacity=capacity,
                        curtailment=curtailment,
                        load=load,
                        annual_load=annual_load
                        )    
    
    logger.info(specs_meta_data)
    print(specs_meta_data)
    return specs
        
    
