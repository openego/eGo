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
This file is part of the the eGo toolbox.
It contains the class definition for multiple eDisGo networks.
"""
__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc"

# Import
import os
import logging
if not 'READTHEDOCS' in os.environ:
    from egoio.db_tables import model_draft, grid
    from egoio.tools import db
    from edisgo.grid.network import Results, TimeSeriesControl
    from edisgo.tools.edisgo_run import (
        run_edisgo_basic
    )
    from edisgo.grid import tools
    from ego.tools.specs import (
        get_etragospecs_direct
    )
    from ego.tools.mv_cluster import (
        analyze_attributes,
        cluster_mv_grids)
    from tools.utilities import define_logging
    
    import pandas as pd
    from sqlalchemy.orm import sessionmaker


# Logging
logger = logging.getLogger(__name__)


class EDisGoNetworks:
    """
    Performs multiple eDisGo runs and stores the resulting edisgo_grids

    Parameters
    ----------
    json_file : :obj:dict
        Dictionary of the ``scenario_setting.json`` file
    etrago_network: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`

    """

    def __init__(self, json_file, etrago_network):

        conn = db.connection(section='oedb')
        Session = sessionmaker(bind=conn)
        self._session = Session()

        # Genral Json Inputs
        self._json_file = json_file
        self._grid_version = self._json_file['global']['gridversion']

        # eTraGo args
        self._etrago_args = self._json_file['eTraGo']
        self._scn_name = self._etrago_args['scn_name']
        self._pf_post_lopf = self._etrago_args['pf_post_lopf']

        # eDisGo args
        self._edisgo_args = self._json_file['eDisGo']
        self._ding0_files = self._edisgo_args['ding0_files']
        self._choice_mode = self._edisgo_args['choice_mode']

        # Scenario translation
        if self._scn_name == 'Status Quo':
            self._generator_scn = None
        elif self._scn_name == 'NEP 2035':
            self._generator_scn = 'nep2035'
        elif self._scn_name == 'eGo 100':
            self._generator_scn = 'ego100'

        # Versioning
        if self._grid_version is not None:
            self._versioned = True
        else:
            self._versioned = False

        # eTraGo Results (Input)
        self._etrago_network = etrago_network

        # eDisGo Results
        self._edisgo_grids = {}

        # Execute Functions
        self._set_grid_choice()
        self._run_edisgo_pool()

    @property
    def edisgo_grids(self):
        """
        Container for eDisGo grids, including all results

        Returns
        -------
        :obj:`dict` of :class:`edisgo.grid.network.EDisGo`
            Dictionary of eDisGo objects, keyed by MV grid ID

        """
        return self._edisgo_grids

    @property
    def grid_choice(self):
        """
        Container for the choice of MV grids, including their weighting

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`
            Dataframe containing the chosen grids and their weightings

        """
        return self._grid_choice

    def _analyze_cluster_attributes(self):
        """
        Analyses the attributes wind and solar capacity and farthest node
        for clustering.
        """
        analyze_attributes(self._ding0_files)

    def _cluster_mv_grids(self, no_grids):
        """
        Clusters the MV grids based on the attributes, for a given number
        of MV grids

        Parameters
        ----------
        no_grids : int
            Desired number of clusters (of MV grids)

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`
            Dataframe containing the clustered MV grids and their weightings

        """
        attributes_path = self._ding0_files + '/attributes.csv'

        if not os.path.isfile(attributes_path):
            logger.info('Attributes file is missing')
            logger.info('Attributes will be calculated')
            self._analyze_cluster_attributes()

        return cluster_mv_grids(self._ding0_files, no_grids)

    def _check_available_mv_grids(self):
        """
        Checks all available MV grids in the given folder (from the settings)

        Returns
        -------
        :obj:`list`
            List of MV grid ID's

        """
        mv_grids = []
        for file in os.listdir(self._ding0_files):
            if file.endswith('.pkl'):
                mv_grids.append(
                    int(file.replace(
                        'ding0_grids__', ''
                    ).replace('.pkl', '')))

        return mv_grids

    def _set_grid_choice(self):
        """
        Sets the grid choice based on the settings file

        """
        if self._choice_mode == 'cluster':
            no_grids = self._edisgo_args['no_grids']
            logger.info('Clustering to {} MV grids'.format(no_grids))
            cluster = self._cluster_mv_grids(no_grids)

        elif self._choice_mode == 'manual':
            man_grids = self._edisgo_args['manual_grids']
            cluster = pd.DataFrame(
                man_grids,
                columns=['the_selected_network_id'])
            cluster['no_of_points_per_cluster'] = 1
            logger.info(
                'Calculating manually chosen MV grids {}'.format(man_grids)
            )

        elif self._choice_mode == 'all':
            mv_grids = self._check_available_mv_grids()
            cluster = pd.DataFrame(
                mv_grids,
                columns=['the_selected_network_id'])
            cluster['no_of_points_per_cluster'] = 1
            no_grids = len(mv_grids)
            logger.info(
                'Calculating all available {} MV grids'.format(no_grids)
            )

        self._grid_choice = cluster

    def _run_edisgo_pool(self):
        """
        Runs eDisGo for the chosen grids

        """
        logger.warning('Parallelization not implemented yet')
        no_grids = len(self._grid_choice)
        count = 0
        for idx, row in self._grid_choice.iterrows():
            prog = '%.1f' % (count / no_grids * 100)
            logger.info(
                '{} % Calculated by eDisGo'.format(prog)
            )

            mv_grid_id = int(row['the_selected_network_id'])
            logger.info(
                'MV grid {}'.format(mv_grid_id)
            )
            try:
                edisgo_grid = self._run_edisgo(mv_grid_id)
                self._edisgo_grids[
                    mv_grid_id
                ] = edisgo_grid
            except Exception:
                self._edisgo_grids[mv_grid_id] = None
                logger.exception(
                    'MV grid {} failed: \n'.format(mv_grid_id)
                )
            count += 1

    def _run_edisgo(
            self, 
            mv_grid_id, 
            apply_curtailment=False,
            storage_integration=False):
        """
        Performs a single eDisGo run

        Parameters
        ----------
        mv_grid_id : int
            MV grid ID of the ding0 grid

        Returns
        -------
        :class:`edisgo.grid.network.EDisGo`
            Returns the complete eDisGo container, also including results
        """

        logger.info('Calculating interface values')
        logger.info('Scenario: {}'.format(self._scn_name))
        
        bus_id = self._get_bus_id_from_mv_grid(mv_grid_id)
    

        specs = get_etragospecs_direct(
            self._session,
            bus_id,
            self._etrago_network,
            self._scn_name,
            self._pf_post_lopf)

        ding0_filepath = (
            self._ding0_files
            + '/ding0_grids__'
            + str(mv_grid_id)
            + '.pkl')

        if not os.path.isfile(ding0_filepath):
            msg = 'Not MV grid file for MV grid ID: ' + str(mv_grid_id)
            logger.error(msg)
            raise Exception(msg)

        ### Inital grid reinforcements
        logger.info('Initial MV grid reinforcement (worst-case anaylsis)')
        edisgo_grid = run_edisgo_basic(
            ding0_filepath=ding0_filepath,
            generator_scenario=None,
            analysis='worst-case')[0]  # only the edisgo_grid is returned

        logger.info('eTraGo feed-in case')
        edisgo_grid.network.results = Results()

        ### Generator import for NEP 2035 and eGo 100 scenarios
        if self._generator_scn:
            logger.info(
                'Importing generators for scenario {}'.format(
                    self._scn_name)
            )
            edisgo_grid.import_generators(
                generator_scenario=self._generator_scn)
        else:
            logger.info(
                'No generators imported for scenario {}'.format(
                    self._scn_name)
            )
            edisgo_grid.network.pypsa = None

        ### Time Series from eTraGo
        logger.info('Updating eDisGo timeseries with eTraGo values')
        if self._pf_post_lopf:
            logger.info('(Including reactive power)')
            edisgo_grid.network.timeseries = TimeSeriesControl(
                network=edisgo_grid.network,
                timeseries_generation_fluctuating=specs['ren_potential'],
                timeseries_generation_dispatchable=specs['conv_dispatch'],
                timeseries_generation_reactive_power=specs['reactive_power'],
                timeseries_load='demandlib',
                timeindex=specs['conv_dispatch'].index).timeseries
        else:
            logger.info('(Only active power)')
            edisgo_grid.network.timeseries = TimeSeriesControl(
                network=edisgo_grid.network,
                timeseries_generation_fluctuating=specs['ren_potential'],
                timeseries_generation_dispatchable=specs['conv_dispatch'],
                timeseries_load='demandlib',
                timeindex=specs['conv_dispatch'].index).timeseries
                
        ### Curtailment
        if apply_curtailment:
            logger.info('Including Curtailment')
            gens_df = tools.get_gen_info(edisgo_grid.network)
            solar_wind_capacities = gens_df.groupby(
                by=['type', 'weather_cell_id']
            )['nominal_capacity'].sum()

            curt_abs = pd.DataFrame(columns=specs['ren_curtailment'].columns)
            for col in curt_abs:
                curt_abs[col] = (
                    specs['ren_curtailment'][col]
                    * solar_wind_capacities[col])

            edisgo_grid.curtail(curtailment_methodology='curtail_all',
                                timeseries_curtailment=curt_abs)
    #             Think about the other curtailment functions!!!!
        else:
            logger.warning('No curtailment applied') 
        
        ### Storage Integration
        if storage_integration:
            if 'battery_p_series' in specs:
                logger.info('Integrating storages in MV grid.')
                edisgo_grid.integrate_storage(
                        timeseries=specs['battery_p_series'],
                        position='distribute_storages_mv',
                        timeseries_reactive_power=None)
        
        edisgo_grid.analyze()
        logger.info('Calculating grid expansion costs.')
        edisgo_grid.reinforce()

        return edisgo_grid

    def _get_mv_grid_from_bus_id(self, bus_id):
        """
        Queries the MV grid ID for a given eTraGo bus

        Parameters
        ----------
        bus_id : int
            eTraGo bus ID

        Returns
        -------
        int
            MV grid (ding0) ID

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

    def _get_bus_id_from_mv_grid(self, subst_id):
        """
        Queries the eTraGo bus ID for given MV grid (ding0) ID

        Parameters
        ----------
        subst_id : int
            MV grid (ding0) ID

        Returns
        -------
        int
            eTraGo bus ID

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
