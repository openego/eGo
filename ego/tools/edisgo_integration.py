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
from edisgo.grid.network import Results
from edisgo.tools.edisgo_run import (
        run_edisgo_basic
        )
from ego.tools.specs import (get_etragospecs_direct)

## Other Packages
import os
import logging
from sqlalchemy.orm import sessionmaker

# Logging
logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        self._ding0_files = self._edisgo_args['ding0_files']
        self._scn_name = self._edisgo_args['scn_name']
        
        if self._scn_name == 'Status Quo':
            self._generator_scn = None
        if self._scn_name == 'NEP 2035':
            self._generator_scn = 'nep2035'
        elif self._scn_name == 'eGo100':
            raise NotImplementedError
        
        if self._grid_version is not None:
            self._versioned = True 
        else:
            self._versioned = False
        
        self._etrago_network = kwargs.get('etrago_network', None)

        
    def check_available_mv_grids(self):
       
        mv_grids = []
        for file in os.listdir(self._ding0_files):
            if file.endswith('.pkl'):
                mv_grids.append(
                        int(file.replace(
                                'ding0_grids__', ''
                                ).replace('.pkl', '')))   
 
        return mv_grids
        
        
    def run_edisgo(self, mv_grid_id):
        """
        Runs eDisGo with the desired settings 
        
        """      
 
        bus_id = self.get_bus_id_from_mv_grid(mv_grid_id)
        
        specs = get_etragospecs_direct(
                self._session, 
                bus_id, 
                self._etrago_network,
                self._scn_name)    
        
        return specs
        
#        ding0_filepath = (
#                self._ding0_files 
#                + '/ding0_grids__' 
#                + str(mv_grid_id) 
#                + '.pkl')
#        
#        if not os.path.isfile(ding0_filepath):
#            msg =  'Not MV grid file for MV grid ID: ' + str(mv_grid_id)
#            logger.error(msg)
#            raise Exception(msg)
#            
#        
        
#        ### Base case with no generator import (initial reinforcement)
#        edisgo_grid, \
#        costs_before_geno_import, \
#        grid_issues_before_geno_import = run_edisgo_basic(
#                ding0_filepath=ding0_filepath,
#                generator_scenario=None,
#                analysis='worst-case')
#         
#        ### Second run for corresponding scenario
#        edisgo_grid.network.results = Results()
#        edisgo_grid.network.pypsa = None
#        
#        if self._generator_scn:
#            edisgo_grid.import_generators(
#                    generator_scenario=self._generator_scn)
            
            

        
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
        
        
        
        
        
        
test = EDisGoNetworks(
        json_file=ego.json_file, 
        etrago_network=ego.etrago_network)   

#        
#test._edisgo_args
ed = test.run_edisgo(mv_grid_id=1729)
#
#ed.network.results.equipment_changes

#test._session
#t = test.get_mv_grid_from_bus_id(25214)
#test.get_bus_id_from_mv_grid(168)
#print(t)
