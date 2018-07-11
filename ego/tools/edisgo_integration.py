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
from edisgo.grid.network import Results, TimeSeriesControl
from edisgo.tools.edisgo_run import (
        run_edisgo_basic
        )
from ego.tools.specs import (
        get_etragospecs_direct,
#        get_feedin_fluctuating,
#        get_curtailment
        )
from ego.tools.mv_cluster import (
        analyze_attributes,
        cluster_mv_grids)

## Other Packages
import os
import logging
from sqlalchemy.orm import sessionmaker

# Logging
logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

class EDisGoNetworks:
    """
    Represents multiple eDisGo networks.

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
        elif self._scn_name == 'NEP 2035':
            self._generator_scn = 'nep2035'
        elif self._scn_name == 'eGo100':
            self._generator_scn = 'ego100'
        
        if self._grid_version is not None:
            self._versioned = True 
        else:
            self._versioned = False
        
        self._etrago_network = kwargs.get('etrago_network', None)

       
    def analyze_cluster_attributes(self):
        """
        Analyses the attributes wind and solar capacity and farthest node
        for clustering.
        """
        analyze_attributes(self._ding0_files)
        
    def cluster_mv_grids(self, no_grids):
        """
        Clusters the MV grids based on the attributes

        """        
        attributes_path = self._ding0_files + '/attributes.csv'
        
        if not os.path.isfile(attributes_path):
            logger.info('Attributes file is missing')
            logger.info('Attributes will be calculated')
            self.analyze_cluster_attributes()

        self._cluster = cluster_mv_grids(self._ding0_files, no_grids)
        
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
        Runs eDisGo with the desired settings. 
        
        """      
 
        logger.info('Calculating interface values')
        bus_id = self.get_bus_id_from_mv_grid(mv_grid_id)
        
        specs = get_etragospecs_direct(
                self._session, 
                bus_id, 
                self._etrago_network,
                self._scn_name)    
        
        ding0_filepath = (
                self._ding0_files 
                + '/ding0_grids__' 
                + str(mv_grid_id) 
                + '.pkl')

        if not os.path.isfile(ding0_filepath):
            msg =  'Not MV grid file for MV grid ID: ' + str(mv_grid_id)
            logger.error(msg)
            raise Exception(msg)
            
                
        logger.info('Initial MV grid reinforcement (starting grid)')
        edisgo_grid, \
        costs_before_geno_import, \
        grid_issues_before_geno_import = run_edisgo_basic(
                ding0_filepath=ding0_filepath,
                generator_scenario=None,
                analysis='worst-case')
         
        logger.info('eTraGo feed-in case')
        edisgo_grid.network.results = Results()
        edisgo_grid.network.pypsa = None
        
        if self._generator_scn:
            edisgo_grid.import_generators(
                    generator_scenario=self._generator_scn)
                  
        edisgo_grid.network.timeseries = TimeSeriesControl( 
                # Here, I use only normalized values from specs
                timeseries_generation_fluctuating=specs['potential'],
                timeseries_generation_dispatchable=specs['conv_dispatch'],
                timeseries_load='demandlib',
                weather_cell_ids=edisgo_grid.network.mv_grid._weather_cells,
                config_data=edisgo_grid.network.config,
                timeindex=specs['conv_dispatch'].index).timeseries
                  
#        edisgo_grid.curtail(curtailment_methodology='curtail_all',
#                            # Here, I use absolute values
#                            timeseries_curtailment=specs['curtailment_abs']) 
        # Think about the other curtailment functions!!!!
        
        edisgo_grid.network.pypsa = None
        
        edisgo_grid.analyze()
        
        
        
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

    
        
        
        
  
test = EDisGoNetworks(
        json_file=ego.json_file, 
        etrago_network=ego.etrago_network)   

test.run_edisgo(mv_grid_id=1729)


