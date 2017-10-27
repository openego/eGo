""" Tests Specs """


#%% Import

    # General Packages
from sqlalchemy import create_engine
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
#from sqlalchemy.ext.automap import automap_base # For automapping
import pandas as pd    
import numpy as np

import logging # ToDo: Logger should be set up more specific
logging.getLogger().setLevel(logging.WARNING)


    # Project Packages
from egoio.db_tables import model_draft # This gives me the specific ORM classes.

from edisgo.grid.network import ETraGoSpecs # ToDo: This needs to be replaced by proper eDisGo installation
#from specs_test import ETraGoSpecs

#%% DB Connection

    # Arguments
bus_id = 24159#104 # This is the bus ID where the corresponding DistG. is connected
result_id = 1

    # Session
# The session functionality can be found in etrago.utilities.oedb_session (and then takes connection from config.ini or in eDisGo case from somewhere else...)
user = "postgres"
password = ""
host = "localhost"
port = "5432"
database = "oedb"

engine = create_engine(
            'postgresql://' + '%s:%s@%s:%s/%s' % (user,
                                                  password,
                                                  host,
                                                  port,
                                                  database))


Session = sessionmaker(bind=engine)
session = Session()


#%% Data import

    # Automapper
    
#_schema = 'model_draft' # If automapped, schema is needed
#_meta = MetaData(schema=_schema)
#Base = automap_base(bind=engine, metadata=_meta) # This is an Automapper that automatically maps the classes from the database (and doesn't consider the explicit orm classes e.g. from model_draft in egoio.db_tables)
#Base.prepare(engine, reflect=True)
#
#_ormclass_result_bus = Base.classes.ego_grid_pf_hv_result_bus


    # Explicit Mapping (No Automapping)
    
ormclass_result_meta = model_draft.__getattribute__('EgoGridPfHvResultMeta')
ormclass_result_bus = model_draft.__getattribute__('EgoGridPfHvResultBus') # Instead of using the automapper, this is the explicit alternative (from egoei.db_tables). IThis class must be identic with the actual database table
#ormclass_resultbus = model_draft.EgoGridPfHvResultBus # This is equivalent
ormclass_result_bus_t = model_draft.__getattribute__('EgoGridPfHvResultBusT')
ormclass_result_gen = model_draft.__getattribute__('EgoGridPfHvResultGenerator')
ormclass_result_gen_t = model_draft.__getattribute__('EgoGridPfHvResultGeneratorT')
ormclass_result_load = model_draft.__getattribute__('EgoGridPfHvResultLoad')
ormclass_result_load_t = model_draft.__getattribute__('EgoGridPfHvResultLoadT')


# ToDo: All the other tables need to be added here...
 

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
#for i in snap_idx:
#    print (i)

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

query = session.query(
        ormclass_result_bus_t.p
        ).filter(
        ormclass_result_bus_t.bus_id == bus_id, # WHERE bus_id AND result_id
        ormclass_result_bus_t.result_id == result_id
        ).scalar(
                )
reactive_power_kvar = pd.Series(
        data=(np.array(query) * 1000 ),# PyPSA result is in MW
        index=snap_idx)

        # Generators     
query = session.query(
        ormclass_result_gen.generator_id # Returns only generator_id column
        ).filter(
        ormclass_result_gen.bus == bus_id)
gen_ids = []
for row in query:
    gen_ids.append(row.generator_id)

# Why is there no source information in database? This is needed for dispatch         
logging.warning("No source/carrier information (generator dispatch and capacity cannot be calculated)")
dispatch = None # Seems like information of generator connection is not in DB results
capacity = None # Needs information about generator connection. Why in SH there are several identic gens (e.G. wind) at one bus?


        # Load
query = session.query(
        ormclass_result_load.load_id # Returns only generator_id column
        ).filter(
        ormclass_result_load.bus == bus_id)
load_ids = []
for row in query:
    load_ids.append(row.load_id)
    
# Why is there no source information in database? This is needed for dispatch         
logging.warning("No type information (load by sector cannot be calculated)")
load = None 
annual_load = None    

        # Storage
battery_capacity = None # No corresponding value in PyPSA found yet...
battery_active_power = None # In PyPSA there is Storage Unit and Strore, which one is represented in the DB table?


  

#%% Return Specs

#specs = ETraGoSpecs(active_power=active_power, ........) # ToDo: All arguments need to be added...    



#%% Cheating Section...

## engine = create_engine('sqlite:///:memory:', echo=True) #SQL is logged (echo)
# In Memory Database...
#engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/test')
  
#
#Base = declarative_base() # Base ist die Basisklasse auf der z.B. alle Tabellenklassen aufbauen. 
#
#
#class User(Base):# Hierbei handelt es sich praktisch um eine ganz normale Python-klasse
#     __tablename__ = 'users'
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     fullname = Column(String)
#     password = Column(String)
#
#     def __repr__(self):
#        return "<User(name='%s', fullname='%s', password='%s')>" % (
#                             self.name, self.fullname, self.password)
#
#
#
#Base.metadata.create_all(engine) # Jetzt werden aus der Klasse alle Tabellen erstellt.
#
#ed_user = User(name='eddy', fullname='Ed Jones', password='edspassword') # Simply an instance of the USER Class
#
#print(ed_user.name)
#
## Now we can start "talking to our database":
#
#session.add(ed_user) #  Instance is now pending     
#
#our_user = session.query(User).filter_by(name='ed').first()
#print(our_user)
#
#session.add_all([
#        User(name='wendy', fullname='Wendy Williams', password='foobar'),
#        User(name='mary', fullname='Mary Contrary', password='xxg527'),
#        User(name='fred', fullname='Fred Flinstone', password='blah')])
#    
#ed_user.password = 'f8s7ccs' #  Session bekommt das mit, benötigt aber einen Commit
#
#session.commit() # Commit wird vor Query automatisch durchgeführt.
#
#ed_user.id #  Primary key wurde in der Datenbank angewendet
#

# Queries:


    

