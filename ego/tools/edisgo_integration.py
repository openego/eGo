"""
This file is part of the the eGo toolbox. 
It contains the class definition for multiple eDisGo networks and results. 

"""
__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc"

# Import
## Local Packages

## Project Packages
from egoio.db_tables import model_draft, grid
from egoio.tools import db
from edisgo.tools.edisgo_run import (
        run_edisgo_basic
        )

## Other Packages
from sqlalchemy.orm import sessionmaker

class EDisGoNetworks:
    """
    Represents multiple eDisGo networks

    """

    def __init__(self, **kwargs):
        
        conn = db.connection(section='oedb')
        Session = sessionmaker(bind=conn)
        self._session = Session()

        self._json_file = kwargs.get('json_file', None)
        
        self._grid_version = self._json_file['global']['gridversion']
        self._edisgo_args = self._json_file['eDisGo']
        
        if self._grid_version is not None:
            self._versioned = True 
        else:
            self._versioned = False
        
        self._etrago_network = kwargs.get('etrago_network', None)
        
  
    def run_edisgo(self, **kwargs):
        
        
        run_edisgo_basic()
        
        # Hier implementieren, so wie twice, aber mit etrago.
        # Reinforce mit Status quo worst case
        # specs klasse umgehen!
        raise NotImplementedError
        
        
## Helpful tools         
    def get_mv_grid_from_bus_id(self, bus_id):
        """
        Returns the MV grid ID for a given eTraGo bus

        """

        if self._versioned is True:
            ormclass_hvmv_subst = grid.__getattribute__(
                    'EgoDpHvmvSubstation'
                    )
            subst_id = self._session.query(
                    ormclass_hvmv_subst.subst_id
                    ).filter(
                            ormclass_hvmv_subst.otg_id == bus_id,
                            ormclass_hvmv_subst.version == self._grid_version
                            ).scalar()

        if self._versioned is False:
            ormclass_hvmv_subst = model_draft.__getattribute__(
                    'EgoGridHvmvSubstation'
                    )
            subst_id = self._session.query(
                    ormclass_hvmv_subst.subst_id
                    ).filter(
                            ormclass_hvmv_subst.otg_id == bus_id
                            ).scalar()          
        
        return subst_id
            
    def get_bus_id_from_mv_grid(self, subst_id):
        """
        Returns the eTraGo bus ID for a given MV grid

        """
        if self._versioned is True:
            ormclass_hvmv_subst = grid.__getattribute__(
                    'EgoDpHvmvSubstation'
                    )
            bus_id = self._session.query(
                    ormclass_hvmv_subst.otg_id
                    ).filter(
                            ormclass_hvmv_subst.subst_id == subst_id,
                            ormclass_hvmv_subst.version == self._grid_version
                            ).scalar()

        if self._versioned is False:
            ormclass_hvmv_subst = model_draft.__getattribute__(
                    'EgoGridHvmvSubstation'
                    )
            bus_id = self._session.query(
                    ormclass_hvmv_subst.otg_id
                    ).filter(
                            ormclass_hvmv_subst.subst_id == subst_id
                            ).scalar()          
        
        return bus_id       

    def get_hvmv_translation(self):
        raise NotImplementedError


     # Hier clustering usw.       
        
        
        
        
        
        
#test = EDisGoNetworks(ego.session, json_file=ego.json_file)   
#        
#test._edisgo_args
#test._session
#t = test.get_mv_grid_from_bus_id(25214)
#test.get_bus_id_from_mv_grid(168)
#print(t)
