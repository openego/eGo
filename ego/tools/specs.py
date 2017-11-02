# Import

    # General Packages
    
import pandas as pd    
import numpy as np
import logging # ToDo: Logger should be set up more specific
logging.getLogger().setLevel(logging.WARNING)

    # Project Packages
    
from egoio.db_tables import model_draft # This gives me the specific ORM classes.
from edisgo.grid.network import ETraGoSpecs # ToDo: This needs to be replaced by proper eDisGo installation
#from tools.specs_test import ETraGoSpecs


# Function Definition

def get_etragospecs(session, 
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
    
    specs_meta_data = {} # Empty dict that gets filled with interesting metadata
    
    # Data import
    
        # Explicit Mapping (No Automapping)
        
    ormclass_result_meta = model_draft.__getattribute__('EgoGridPfHvResultMeta')
    #ormclass_result_bus = model_draft.__getattribute__('EgoGridPfHvResultBus') # Instead of using the automapper, this is the explicit alternative (from egoei.db_tables). IThis class must be identic with the actual database table
    #ormclass_result_bus = model_draft.EgoGridPfHvResultBus # This is equivalent
    ormclass_result_bus_t = model_draft.__getattribute__('EgoGridPfHvResultBusT')
    ormclass_result_gen = model_draft.__getattribute__('EgoGridPfHvResultGenerator')
    ormclass_result_gen_t = model_draft.__getattribute__('EgoGridPfHvResultGeneratorT')
    ormclass_result_load = model_draft.__getattribute__('EgoGridPfHvResultLoad')
    ormclass_result_load_t = model_draft.__getattribute__('EgoGridPfHvResultLoadT')
    ormclass_result_stor = model_draft.__getattribute__('EgoGridPfHvResultStorage')
    ormclass_result_stor_t = model_draft.__getattribute__('EgoGridPfHvResultStorageT')
    ormclass_source = model_draft.__getattribute__('EgoGridPfHvSource')
    
        # Import Data from DB tables
        
    start_snapshot = session.query( # Scalar Value (first Timestep)
            ormclass_result_meta.start_snapshot
            ).filter(
            ormclass_result_meta.result_id == result_id
            ).scalar(
                    ) 
     
    end_snapshot = session.query( # Scalar Value (last Timestep)
            ormclass_result_meta.end_snapshot
            ).filter(
            ormclass_result_meta.result_id == result_id
            ).scalar( # directly returns scalar value, since there is only one column on this. ToDo: Make more conventional!
                    )
     
    snap_idx = range(start_snapshot, end_snapshot + 1) # Range including all timesteps, used for indexing
    
            # Buses
    query = session.query(
            ormclass_result_bus_t.p
            ).filter(
            ormclass_result_bus_t.bus_id == bus_id, # WHERE bus_id AND result_id
            ormclass_result_bus_t.result_id == result_id
            ).scalar( # Returns first element of single queried row
                    )
    active_power_kW = pd.Series( # bus active power 
            data=(np.array(query) * 1000 ), # PyPSA result is in MW
            index=snap_idx) # Index of series is the exact used timestep
    
    #query = session.query(
    #        ormclass_result_bus_t.q
    #        ).filter(
    #        ormclass_result_bus_t.bus_id == bus_id, # WHERE bus_id AND result_id
    #        ormclass_result_bus_t.result_id == result_id
    #        ).scalar(
    #                )
    #reactive_power_kvar = pd.Series(
    #        data=(np.array(query) * 1000 ),# PyPSA result is in MW
    #        index=snap_idx)
    
    reactive_power_kvar = pd.Series( # ToDo: Quick fix for non existent Q. better none and Abfrage ob LOPF
            data=None,
            index=snap_idx)
    
            # Generators     
    query = session.query(
            ormclass_result_gen.generator_id # Returns only generator_id column
            ).filter(
            ormclass_result_gen.bus == bus_id)
    gen_ids = []
    for row in query:
        gen_ids.append(row.generator_id)
           
    gen_sources = []
    for id in gen_ids:   
        query = session.query(ormclass_source.name
                  ).filter(
                          ormclass_source.source_id==ormclass_result_gen.source
                          ).filter(
                                  ormclass_result_gen.generator_id==id).scalar()
        gen_sources.append(query)
      
                # Generator Capacity
    capacity = pd.DataFrame(0.0, index=['Capacity'], columns=list(set(gen_sources)))
    
    for i, gen_id in enumerate(gen_ids):
        
        source = gen_sources[i]
        gen_capacity_MW = session.query(
                ormclass_result_gen.p_nom
                ).filter(
                ormclass_result_gen.generator_id == gen_id
                ).scalar(
                        )
    
        capacity[source]['Capacity'] = capacity[source]['Capacity'] + gen_capacity_MW
    
                # Generator Dispatch (Normalized)
    dispatch = pd.DataFrame(0.0, index=snap_idx, columns=list(set(gen_sources))) # Makes dataframe with only zeros, unique columns form sources and snap_idx form snapshots)
    
    for i, gen_id in enumerate(gen_ids):
        
        source = gen_sources[i]
        query = session.query(
                ormclass_result_gen_t.p
                ).filter(
                ormclass_result_gen_t.generator_id == gen_id
                ).scalar(
                        )
    
        gen_series_norm = pd.Series(
                data=(np.array(query) / capacity[source]['Capacity'] ), # Every generator normalized by installed capacity.
                index=snap_idx)
        
        for snap in snap_idx:
            dispatch[source][snap] = dispatch[source][snap] + gen_series_norm[snap] # Aggregatet by source (adds up)
        
    
            # Load
    query = session.query(
            ormclass_result_load.load_id 
            ).filter(
            ormclass_result_load.bus == bus_id)
    load_ids = []
    for row in query:
        load_ids.append(row.load_id)
        
    load_types = ['all'] # ToDo: This is in eTraGo still not implemented
    
                # Annual Load
    annual_load = pd.DataFrame(0.0, index=['Annual Load'], columns=list(set(load_types)))
    
    for i, load_id in enumerate(load_ids):
        
        load_type = load_types[i]
        annual_load_MWh = session.query( # ToDo: Check unit
                ormclass_result_load.e_annual
                ).filter(
                ormclass_result_load.load_id == load_id
                ).scalar(
                        ) * 1000 # eTraGo annual load apparently in GWh    
        
        annual_load[load_type]['Annual Load'] = annual_load[load_type]['Annual Load'] + annual_load_MWh
    
                # Load series
    load = pd.DataFrame(0.0, index=snap_idx, columns=list(set(load_types)))
    
    for i, load_id in enumerate(load_ids):
        
        load_type = load_types[i]
        query = session.query(
                ormclass_result_load_t.p
                ).filter(
                ormclass_result_load_t.load_id == load_id
                ).scalar(
                        )
    
        load_series_norm = pd.Series(
                data=(np.array(query) / annual_load[load_type]['Annual Load'] ), # ToDo: Check Units!!!
                index=snap_idx)
        
        for snap in snap_idx:
            load[load_type][snap] = load[load_type][snap] + load_series_norm[snap] # Aggregatet by source (adds up)
        
             # Storage    
    query = session.query(
            ormclass_result_stor.storage_id # More than one storage device is possible...
            ).filter(
            ormclass_result_stor.bus == bus_id)
    stor_ids = []
    for row in query:
        stor_ids.append(row.storage_id)
        
    stor_sources = []
    for id in stor_ids:   
        query = session.query(ormclass_source.name
                  ).filter(
                          ormclass_source.source_id==ormclass_result_stor.source
                          ).filter(
                                  ormclass_result_stor.storage_id==id).scalar()
        stor_sources.append(query)
   
    specs_meta_data.update({'Number of extendable storages at this bus':stor_sources.count('extendable_storage')})
    
                # Storage Capacity
    stor_capacity = pd.DataFrame(0.0, 
                                 index=['Stor_capacity'], 
                                 columns=list(set(stor_sources)))
    
    for i, stor_id in enumerate(stor_ids):
        
        source = stor_sources[i]
        p_nom_opt_MW = session.query(
                ormclass_result_stor.p_nom_opt
                ).filter(
                ormclass_result_stor.storage_id == stor_id
                ).scalar(
                        )
    
        max_hours = session.query(
                ormclass_result_stor.max_hours
                ).filter(
                ormclass_result_stor.storage_id == stor_id
                ).scalar(
                        )
        
        stor_capacity[source]['Stor_capacity'] = stor_capacity[source]['Stor_capacity'] + p_nom_opt_MW * max_hours
            
                # Storage Active Power
    stor_active_power = pd.DataFrame(0.0, 
                                        index=snap_idx, 
                                        columns=list(set(stor_sources)))
    
    for i, stor_id in enumerate(stor_ids):
        
        source = stor_sources[i]
        query = session.query(
                ormclass_result_stor_t.p
                ).filter(
                ormclass_result_stor_t.storage_id == stor_id
                ).scalar(
                        )
        stor_active_power_series_kW = pd.Series( # bus active power 
            data=(np.array(query) * 1000 ), # PyPSA result is in MW
            index=snap_idx)
    
        for snap in snap_idx:
            stor_active_power[source][snap] = stor_active_power[source][snap] + stor_active_power_series_kW[snap] # Aggregatet by source (adds up) 
        
    
    # Return Specs
    
    specs = ETraGoSpecs(active_power=active_power_kW,
                        reactive_power=reactive_power_kvar,
                        battery_capacity=stor_capacity['extendable_storage']['Stor_capacity'],
                        battery_active_power=stor_active_power['extendable_storage'], # ToDo: Check if extendable_storage is battery!
                        dispatch=dispatch,
                        capacity=capacity,
                        load=load,
                        annual_load=annual_load
                        )    
    
    return specs
        
    
