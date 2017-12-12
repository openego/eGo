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

# Function Attributes
from sqlalchemy.orm import sessionmaker
from sqlalchemy import distinct
    
from oemof import db
conn = db.connection(section='oedb')

Session = sessionmaker(bind=conn)
session = Session()

bus_id = 26930
result_id = 9


#def get_etragospecs_from_db(session, 
#                            bus_id, 
#                            result_id=1):
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
## Capacity
    # Todo: This query needs to be adjusted, since some generators can have more than one w_id...
    query = session.query( # ToDo: This query is very slow. This might be problematic if the interface is used for all TG buses at once...
            distinct(ormclass_result_gen.generator_id).label('generator_id'), # This ID is an aggregate ID (single generators aggregated)
            ormclass_result_gen.p_nom,
            ormclass_source.name,
            ormclass_result_gen_single.w_id # weather ID for specific dispatch of RE per w_id
            ).join(
                    ormclass_source, 
                    ormclass_source.source_id == ormclass_result_gen.source
                    ).outerjoin( # Must be outer join, cause of load shedders etc.
                    ormclass_result_gen_single,
                    ormclass_result_gen_single.aggr_id == ormclass_result_gen.generator_id
                    ).filter(
                            ormclass_result_gen.bus == bus_id,
                            ormclass_result_gen.result_id == result_id,
                            ormclass_result_gen_single.scn_name == scn_name)
  
    gen_df = pd.DataFrame(query.all(), 
                          columns=[column['name'] for 
                                   column in 
                                   query.column_descriptions]) 
     
    generators = gen_df[['generator_id', 'name', 'w_id']]
    
## Dispatch and Curtailment    
    query = session.query(
            ormclass_result_gen_t.generator_id, # This is an aggregated generator ID (see ego_dp_powerflow_assignment_generator for info)
            ormclass_result_gen_t.p,
            ormclass_result_gen_t.p_max_pu # The maximum output for each snapshot per unit of p_nom for the OPF (e.g. for variable renewable generators this can change due to weather conditions; for conventional generators it represents a maximum dispatch)
            ).filter(
            ormclass_result_gen_t.generator_id.in_(gen_df['generator_id']),
            ormclass_result_gen_t.result_id == result_id
            )     
    
    gen_t_df = pd.DataFrame(query.all(), 
                            columns=[column['name'] for 
                                     column in 
                                     query.column_descriptions]) 
    
    dispatch = pd.DataFrame(0.0, 
                            index=snap_idx, 
                            columns=list(set(gen_df['generator_id'])))
    curtailment = pd.DataFrame(0.0, 
                            index=snap_idx, 
                            columns=list(set(gen_t_df.dropna(
                                    subset=['p_max_pu']
                                    )['generator_id']))) 
    
    
    for index, row in gen_t_df.iterrows():
        generator_id = row['generator_id']
        print(generator_id)
        p_nom = float(gen_df[gen_df['generator_id'] == generator_id]['p_nom'])
        
        gen_series_norm = pd.Series(
                data=[x/p_nom for x in row['p']], # Every generator normalized by total installed capacity.
                index=snap_idx)
        
        dispatch[generator_id] = gen_series_norm
        
        p_max_pu = row['p_max_pu'] 
        if p_max_pu is not None:
            curt_series_norm = p_max_pu - gen_series_norm
            
            curtailment[generator_id] = curt_series_norm
            
      
    
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
    
    storage = stor_df[['storage_id', 'name', 'capacity_MWh', 'p_nom_opt']]
    if count_bat > 1:
        logger.warning('More than one Battery at bus %s' %specs_meta_data.get('TG Bus ID')) 
    
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
        
    state_of_charge = pd.DataFrame(0.0,
                               index=snap_idx,
                               columns=list(set(stor_df['storage_id'])))
    
    stor_dispatch = pd.DataFrame(0.0,
                               index=snap_idx,
                               columns=list(set(stor_df['storage_id'])))
    

    for index, row in stor_t_df.iterrows():
        stor_id = row['storage_id']
        p_nom_opt = float(stor_df[stor_df['storage_id'] == stor_id]['p_nom_opt'])
        if p_nom_opt == 0.0:
            stor_series_norm = pd.Series(0.0, index = snap_idx)
        else:
            stor_series_norm = pd.Series(
                data=[x/p_nom_opt for x in row['p']], # Every generator normalized by total installed capacity.
                index=snap_idx)
        
        stor_dispatch[stor_id] = stor_series_norm
        
        stor_cap = float(stor_df[stor_df['storage_id'] == stor_id]['capacity_MWh'])
        if stor_cap == 0.0:
            soc_series_norm = pd.Series(0.0, index = snap_idx)
        else:
            soc_series_norm = pd.Series(
                data=[x/stor_cap for x in row['state_of_charge']], # Every generator normalized by total installed capacity.
                index=snap_idx)
        
        state_of_charge[stor_id] = soc_series_norm
        
except:
    logger.exception("Storage could not be queried for \
                     Specs with Metadata: \n %s" %specs_meta_data)        

 
# Return Specs

specs = ETraGoSpecs(#generators...
                    )    

logger.info(specs_meta_data)
#return specs
    
    
