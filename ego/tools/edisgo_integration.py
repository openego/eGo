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
from traceback import TracebackException
import os
import pickle
import logging
import traceback
import pypsa
import csv
import dill
import pandas as pd
from time import localtime, sleep, strftime
from datetime import datetime, timedelta as td
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
import multiprocess as mp2

if not 'READTHEDOCS' in os.environ:

    from egoio.db_tables import model_draft, grid
    from egoio.tools import db

    from edisgo.grid.network import Results, TimeSeriesControl
    from edisgo.grid import tools
    from edisgo.tools.plots import mv_grid_topology
    from edisgo.grid.network import EDisGo

    from ego.tools.specs import (
        get_etragospecs_direct
    )
    from ego.tools.mv_cluster import (
        analyze_attributes,
        cluster_mv_grids)
    from ego.tools.economics import (
        edisgo_grid_investment)


# Logging
logger = logging.getLogger(__name__)

pickle.DEFAULT_PROTOCOL = 4
dill.settings['protocol'] = 4


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

        # Genral Json Inputs
        self._json_file = json_file
        self._set_scenario_settings()

        # Create reduced eTraGo network
        self._etrago_network = _ETraGoData(etrago_network)
        del etrago_network

        # eDisGo specific naming
        self._edisgo_scenario_translation()

        # Program information
        self._run_finished = False

        # eDisGo Result grids
        self._edisgo_grids = {}

        if self._csv_import:
            self._laod_edisgo_results()
            self._successfull_grids = self._successfull_grids()
            self._grid_investment_costs = edisgo_grid_investment(
                self,
                self._json_file
            )

        else:
            # Only clustering results
            if self._only_cluster:
                self._set_grid_choice()
                if self._results:
                    self._save_edisgo_results()
                self._grid_investment_costs = None

            else:
                # Execute Functions
                self._set_grid_choice()
                self._init_status()
                self._run_edisgo_pool()
                if self._results:
                    self._save_edisgo_results()

                self._successfull_grids = self._successfull_grids()

                self._grid_investment_costs = edisgo_grid_investment(
                    self,
                    self._json_file
                )

    @property
    def network(self):
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

    @property
    def successfull_grids(self):
        """
        Relative number of successfully calculated MV grids
        (Includes clustering weighting)

        Returns
        -------
        int
            Relative number of grids

        """
        return self._successfull_grids

    @property
    def grid_investment_costs(self):
        """
        Grid investment costs

        Returns
        -------
        None or :pandas:`pandas.DataFrame<dataframe>`
            Dataframe containing annuity costs per voltage level

        """
        return self._grid_investment_costs

    def get_mv_grid_from_bus_id(self, bus_id):
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

        conn = db.connection(section=self._db_section)
        session_factory = sessionmaker(bind=conn)
        Session = scoped_session(session_factory)
        session = Session()

        mv_grid_id = self._get_mv_grid_from_bus_id(session, bus_id)

        Session.remove()

        return mv_grid_id

    def get_bus_id_from_mv_grid(self, subst_id):
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

        conn = db.connection(section=self._db_section)
        session_factory = sessionmaker(bind=conn)
        Session = scoped_session(session_factory)
        session = Session()

        bus_id = self._get_bus_id_from_mv_grid(session, subst_id)

        Session.remove()

        return bus_id

    def plot_storage_integration(self, mv_grid_id, **kwargs):
        """
        Plots storage position in MV grid of integrated storages.
        For more information see :func:`edisgo.tools.plots.mv_grid_topology`.
        """
        mv_grid_topology(
            self._edisgo_grids[mv_grid_id].network.pypsa,
            self._edisgo_grids[mv_grid_id].network.config,
            node_color=kwargs.get('storage_integration', None),
            filename=kwargs.get('filename', None),
            grid_district_geom=kwargs.get('grid_district_geom', True),
            background_map=kwargs.get('background_map', True),
            xlim=kwargs.get('xlim', None), ylim=kwargs.get('ylim', None),
            title=kwargs.get('title', ''))

    def plot_grid_expansion_costs(self, mv_grid_id, ** kwargs):
        """
        Plots costs per MV line.
        For more information see :func:`edisgo.tools.plots.mv_grid_topology`.
        """

        mv_grid_topology(
            self._edisgo_grids[mv_grid_id].network.pypsa,
            self._edisgo_grids[mv_grid_id].network.config,
            line_color='expansion_costs',
            grid_expansion_costs=(
                self._edisgo_grids[mv_grid_id].network.
                results.grid_expansion_costs.rename(columns={
                    "overnight_costs": "total_costs"})),
            filename=kwargs.get('filename', None),
            grid_district_geom=kwargs.get('grid_district_geom', True),
            background_map=kwargs.get('background_map', True),
            limits_cb_lines=kwargs.get('limits_cb_lines', None),
            xlim=kwargs.get('xlim', None), ylim=kwargs.get('ylim', None),
            lines_cmap=kwargs.get('lines_cmap', 'inferno_r'),
            title=kwargs.get('title', ''))

    def plot_line_loading(self, mv_grid_id, **kwargs):
        """
        Plots relative line loading (current from power flow analysis to
        allowed current) of MV lines.
        For more information see :func:`edisgo.tools.plots.mv_grid_topology`.
        """

        mv_grid_topology(
            self._edisgo_grids[mv_grid_id].network.pypsa,
            self._edisgo_grids[mv_grid_id].network.config,
            timestep=kwargs.get('timestep', None),
            line_color='loading',
            node_color=kwargs.get('node_color', None),
            line_load=self._edisgo_grids[mv_grid_id].network.results.s_res(),
            filename=kwargs.get('filename', None),
            arrows=kwargs.get('arrows', None),
            grid_district_geom=kwargs.get('grid_district_geom', True),
            background_map=kwargs.get('background_map', True),
            voltage=None,  # change API
            limits_cb_lines=kwargs.get('limits_cb_lines', None),
            limits_cb_nodes=kwargs.get('limits_cb_nodes', None),
            xlim=kwargs.get('xlim', None), ylim=kwargs.get('ylim', None),
            lines_cmap=kwargs.get('lines_cmap', 'inferno_r'),
            title=kwargs.get('title', ''))

    def plot_mv_grid_topology(self, mv_grid_id, **kwargs):
        """
        Plots plain MV grid topology.
        For more information see :func:`edisgo.tools.plots.mv_grid_topology`.
        """

        mv_grid_topology(self._edisgo_grids[mv_grid_id].network.pypsa,
                         self._edisgo_grids[mv_grid_id].network.config,
                         filename=kwargs.get('filename', None),
                         grid_district_geom=kwargs.get(
                             'grid_district_geom', True),
                         background_map=kwargs.get('background_map', True),
                         xlim=kwargs.get('xlim', None),
                         ylim=kwargs.get('ylim', None),
                         title=kwargs.get('title', ''))

    def _init_status(self):
        """
        Creates a Status file where all eDisGo statuses are tracked...
        """
        self._status_dir = 'status'
        if not os.path.exists(self._status_dir):
            os.makedirs(self._status_dir)

        self._status_file = 'eGo_' + strftime("%Y-%m-%d_%H%M%S", localtime())

        status = self._grid_choice.copy()
        status = status.set_index('the_selected_network_id')
        status.index.names = ['MV grid']

        tot_reprs = self._grid_choice['no_of_points_per_cluster'].sum()

        status['cluster_perc'] = status['no_of_points_per_cluster'] / tot_reprs

        status['start_time'] = 'Not started yet'
        status['end_time'] = 'Not finished yet'

        status.drop(
            ['no_of_points_per_cluster', 'represented_grids'],
            axis=1,
            inplace=True)

        self._status_path = os.path.join(
            self._status_dir,
            self._status_file + '.csv')

        status.to_csv(self._status_path)

    def _status_update(self, mv_grid_id, time, message=None, show=True):
        """
        Updtaed eDisGo's status files
        """
        status = pd.read_csv(
            self._status_path,
            index_col=0)

        status['start_time'] = status['start_time'].astype(str)
        status['end_time'] = status['end_time'].astype(str)

        if message:
            now = message
        else:
            now = strftime("%Y-%m-%d_%H:%M", localtime())

        if time == 'start':
            status.at[mv_grid_id, 'start_time'] = now
        elif time == 'end':
            status.at[mv_grid_id, 'end_time'] = now
        if show:
            logger.info("\n\neDisGo Status: \n\n"
                        + status.to_string()
                        + "\n\n")

        status.to_csv(self._status_path)

    def _update_edisgo_configs(self, edisgo_grid):
        """
        This function overwrites some eDisGo configurations with eGo
        settings.
        """
        # Info and Warning handling
        if not hasattr(self, '_suppress_log'):
            self._suppress_log = False  # Only in the first run warnings and
            # info get thrown

        # Database section
        ego_db = self._db_section
        edisgo_db = edisgo_grid.network.config['db_connection']['section']

        if not ego_db == edisgo_db:
            if not self._suppress_log:
                logger.warning(
                    ("eDisGo database configuration (db: '{}') "
                     + "will be overwritten with database configuration "
                     + "from eGo's scenario settings (db: '{}')").format(
                        edisgo_db,
                        ego_db))
            edisgo_grid.network.config['db_connection']['section'] = ego_db

        # Versioned
        ego_gridversion = self._grid_version
        if ego_gridversion == None:
            ego_versioned = 'model_draft'
            if not self._suppress_log:
                logger.info("eGo's grid_version == None is "
                            + "evaluated as data source: model_draft")
        else:
            ego_versioned = 'versioned'
            if not self._suppress_log:
                logger.info(("eGo's grid_version == '{}' is "
                             + "evaluated as data source: versioned").format(
                    ego_gridversion))

        edisgo_versioned = edisgo_grid.network.config[
            'data_source']['oedb_data_source']

        if not ego_versioned == edisgo_versioned:
            if not self._suppress_log:
                logger.warning(
                    ("eDisGo data source configuration ('{}') "
                     + "will be overwritten with data source config. from "
                     + "eGo's scenario settings (data source: '{}')"
                     ).format(
                        edisgo_versioned,
                        ego_versioned))
            edisgo_grid.network.config[
                'data_source']['oedb_data_source'] = ego_versioned

        # Gridversion
        ego_gridversion = self._grid_version
        edisgo_gridversion = edisgo_grid.network.config[
            'versioned']['version']

        if not ego_gridversion == edisgo_gridversion:
            if not self._suppress_log:
                logger.warning(
                    ("eDisGo version configuration (version: '{}') "
                     + "will be overwritten with version configuration "
                     + "from eGo's scenario settings (version: '{}')"
                     ).format(
                        edisgo_gridversion,
                        ego_gridversion))
            edisgo_grid.network.config[
                'versioned']['version'] = ego_gridversion

        self._suppress_log = True

    def _set_scenario_settings(self):

        self._csv_import = self._json_file['eGo']['csv_import_eDisGo']

        # eTraGo args
        self._etrago_args = self._json_file['eTraGo']
        self._scn_name = self._etrago_args['scn_name']
        self._ext_storage = (
            'storage' in self._etrago_args['extendable']
        )
        if self._ext_storage:
            logger.info("eTraGo Dataset used extendable storage")

        self._pf_post_lopf = self._etrago_args['pf_post_lopf']

        # eDisGo args import
        if self._csv_import:
            #            raise NotImplementedError

            with open(os.path.join(
                    self._csv_import,
                    'edisgo_args.json')) as f:
                edisgo_args = json.load(f)

            self._json_file['eDisGo'] = edisgo_args
            logger.info("All eDisGo settings are taken from CSV folder"
                        + "(scenario settings are ignored)")
            # This overwrites the original object...

        # Imported or directly from the Settings
        # eDisGo section of the settings
        self._edisgo_args = self._json_file['eDisGo']

        # Reading all eDisGo settings
        # TODO: Integrate into a for-loop
        self._db_section = self._edisgo_args['db']
        self._grid_version = self._edisgo_args['gridversion']
        self._timesteps_pfa = self._edisgo_args['timesteps_pfa']
        self._solver = self._edisgo_args['solver']
        self._curtailment_voltage_threshold = self._edisgo_args[
            'curtailment_voltage_threshold']
        self._ding0_files = self._edisgo_args['ding0_files']
        self._choice_mode = self._edisgo_args['choice_mode']
        self._parallelization = self._edisgo_args['parallelization']
        self._initial_reinforcement = self._edisgo_args[
            'initial_reinforcement']
        self._storage_distribution = self._edisgo_args['storage_distribution']
        self._apply_curtailment = self._edisgo_args['apply_curtailment']
        self._cluster_attributes = self._edisgo_args['cluster_attributes']
        self._only_cluster = self._edisgo_args['only_cluster']
        self._max_workers = self._edisgo_args['max_workers']
        self._max_cos_phi_renewable = self._edisgo_args[
            'max_cos_phi_renewable']
        self._results = self._edisgo_args['results']
        self._max_calc_time = self._edisgo_args['max_calc_time']

        # Some basic checks
        if (self._storage_distribution is True) & (self._ext_storage is False):
            logger.warning("Storage distribution (MV grids) is active, "
                           + "but eTraGo dataset has no extendable storages")
        if not self._initial_reinforcement:
            raise NotImplementedError(
                "Skipping the initial reinforcement is not yet implemented"
            )
        if self._only_cluster:
            logger.warning(
                "\n\nThis eDisGo run only returns cluster results\n\n")

        # Versioning
        if self._grid_version is not None:
            self._versioned = True
        else:
            self._versioned = False

    def _edisgo_scenario_translation(self):

        # Scenario translation
        if self._scn_name == 'Status Quo':
            self._generator_scn = None
        elif self._scn_name == 'NEP 2035':
            self._generator_scn = 'nep2035'
        elif self._scn_name == 'eGo 100':
            self._generator_scn = 'ego100'

    def _successfull_grids(self):
        """
        Calculates the relative number of successfully calculated grids,
        including the cluster weightings
        """

        total, success, fail = 0, 0, 0
        for key, value in self._edisgo_grids.items():

            weight = self._grid_choice.loc[
                self._grid_choice['the_selected_network_id'] == key
            ]['no_of_points_per_cluster'].values[0]

            total += weight
            if hasattr(value, 'network'):
                success += weight
            else:
                fail += weight
        return success/total

    def _analyze_cluster_attributes(self):
        """
        Analyses the attributes wind and solar capacity and farthest node
        for clustering.
        These are considered the "standard" attributes for the MV grid
        clustering.
        """
        analyze_attributes(self._ding0_files)

    def _cluster_mv_grids(
            self,
            no_grids):
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

        # TODO: This first dataframe contains the standard attributes...
        # ...Create an Interface in order to use attributes more flexibly.
        # Make this function more generic.
        attributes_path = self._ding0_files + '/attributes.csv'

        if not os.path.isfile(attributes_path):
            logger.info('Attributes file is missing')
            logger.info('Attributes will be calculated')
            self._analyze_cluster_attributes()

        df = pd.read_csv(self._ding0_files + '/attributes.csv')
        df = df.set_index('id')
        df.drop(['Unnamed: 0'], inplace=True, axis=1)
        df.rename(
            columns={
                "Solar_cumulative_capacity": "solar_cap",
                "Wind_cumulative_capacity": "wind_cap",
                "The_Farthest_node": "farthest_node"},
            inplace=True)

        if 'extended_storage' in self._cluster_attributes:
            if self._ext_storage:
                storages = self._identify_extended_storages()
                if not (storages.max().values[0] == 0.):
                    df = pd.concat([df, storages], axis=1)
                    df.rename(
                        columns={"storage_p_nom": "extended_storage"},
                        inplace=True)
                else:
                    logger.warning('Extended storages all 0. \
                                   Therefore, extended storages \
                                   are excluded from clustering')

        found_atts = [
            i for i in self._cluster_attributes if i in df.columns
        ]
        missing_atts = [
            i for i in self._cluster_attributes if i not in df.columns
        ]

        logger.info(
            'Available attributes are: {}'.format(df.columns.tolist())
        )
        logger.info(
            'Chosen/found attributes are: {}'.format(found_atts)
        )

        if len(missing_atts) > 0:
            logger.warning(
                'Missing attributes: {}'.format(missing_atts)
            )
            if 'extended_storage' in missing_atts:
                logger.info('Hint: eTraGo dataset must contain '
                            'extendable storage in order to include '
                            'storage extension in MV grid clustering.')

        return cluster_mv_grids(
            no_grids,
            cluster_base=df)

    def _identify_extended_storages(self):

        conn = db.connection(section=self._db_section)
        session_factory = sessionmaker(bind=conn)
        Session = scoped_session(session_factory)
        session = Session()

        all_mv_grids = self._check_available_mv_grids()

        storages = pd.DataFrame(
            index=all_mv_grids,
            columns=['storage_p_nom'])

        logger.info('Identifying extended storage')
        for mv_grid in all_mv_grids:
            bus_id = self._get_bus_id_from_mv_grid(session, mv_grid)

            min_extended = 0.3
            stor_p_nom = self._etrago_network.storage_units.loc[
                (self._etrago_network.storage_units['bus'] == str(bus_id))
                & (self._etrago_network.storage_units[
                    'p_nom_extendable'
                ] == True)
                & (self._etrago_network.storage_units[
                    'p_nom_opt'
                ] > min_extended)
                & (self._etrago_network.storage_units['max_hours'] <= 20.)
            ]['p_nom_opt']

            if len(stor_p_nom) == 1:
                stor_p_nom = stor_p_nom.values[0]
            elif len(stor_p_nom) == 0:
                stor_p_nom = 0.
            else:
                raise IndexError

            storages.at[mv_grid, 'storage_p_nom'] = stor_p_nom

        Session.remove()

        return storages

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

        choice_df = pd.DataFrame(
            columns=[
                'no_of_points_per_cluster',
                'the_selected_network_id',
                'represented_grids'])

        if self._choice_mode == 'cluster':
            no_grids = self._edisgo_args['no_grids']
            logger.info('Clustering to {} MV grids'.format(no_grids))

            cluster_df = self._cluster_mv_grids(no_grids)
            choice_df[
                'the_selected_network_id'
            ] = cluster_df['the_selected_network_id']
            choice_df[
                'no_of_points_per_cluster'
            ] = cluster_df['no_of_points_per_cluster']
            choice_df[
                'represented_grids'
            ] = cluster_df['represented_grids']

        elif self._choice_mode == 'manual':
            man_grids = self._edisgo_args['manual_grids']

            choice_df['the_selected_network_id'] = man_grids
            choice_df['no_of_points_per_cluster'] = 1
            choice_df['represented_grids'] = [
                [mv_grid_id]
                for mv_grid_id
                in choice_df['the_selected_network_id']]

            logger.info(
                'Calculating manually chosen MV grids {}'.format(man_grids)
            )

        elif self._choice_mode == 'all':
            mv_grids = self._check_available_mv_grids()

            choice_df['the_selected_network_id'] = mv_grids
            choice_df['no_of_points_per_cluster'] = 1
            choice_df['represented_grids'] = [
                [mv_grid_id]
                for mv_grid_id
                in choice_df['the_selected_network_id']]

            no_grids = len(mv_grids)
            logger.info(
                'Calculating all available {} MV grids'.format(no_grids)
            )

        choice_df = choice_df.sort_values(
            'no_of_points_per_cluster',
            ascending=False)

        self._grid_choice = choice_df

    def _run_edisgo_pool(self):
        """
        Runs eDisGo for the chosen grids

        """
        parallelization = self._parallelization

        if not os.path.exists(self._results):
            os.makedirs(self._results)

        if parallelization is True:
            logger.info('Run eDisGo parallel')
            mv_grids = self._grid_choice['the_selected_network_id'].tolist()
            no_cpu = mp2.cpu_count()
            if no_cpu > self._max_workers:
                no_cpu = self._max_workers
                logger.info(
                    'Number of workers limited to {} by user'.format(
                        self._max_workers
                    ))

            self._edisgo_grids = set(mv_grids)
            self._edisgo_grids = parallelizer(
                mv_grids,
                lambda *xs: xs[1]._run_edisgo(xs[0]),
                (self,),
                self._max_calc_time,
                workers=no_cpu)

            for g in mv_grids:
                if not g in self._edisgo_grids:
                    self._edisgo_grids[g] = 'Timeout'

        else:
            logger.info('Run eDisGo sequencial')
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
                except Exception as e:
                    self._edisgo_grids[mv_grid_id] = e
                    logger.exception(
                        'MV grid {} failed: \n'.format(mv_grid_id)
                    )
                count += 1

        self._csv_import = self._json_file['eDisGo']['results']
        self._save_edisgo_results()
        self._laod_edisgo_results()
        self._run_finished = True

    def _run_edisgo(
            self,
            mv_grid_id):
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
        self._status_update(mv_grid_id, 'start', show=False)

        storage_integration = self._storage_distribution
        apply_curtailment = self._apply_curtailment

        logger.info(
            'MV grid {}: Calculating interface values'.format(mv_grid_id))

        conn = db.connection(section=self._db_section)
        session_factory = sessionmaker(bind=conn)
        Session = scoped_session(session_factory)
        session = Session()

        # Query bus ID for this MV grid
        bus_id = self._get_bus_id_from_mv_grid(session, mv_grid_id)

        # Calculate Interface values for this MV grid
        specs = get_etragospecs_direct(
            session,
            bus_id,
            self._etrago_network,
            self._scn_name,
            self._grid_version,
            self._pf_post_lopf,
            self._max_cos_phi_renewable)
        Session.remove()

        # Get ding0 (MV grid) form folder
        ding0_filepath = (
            self._ding0_files
            + '/ding0_grids__'
            + str(mv_grid_id)
            + '.pkl')

        if not os.path.isfile(ding0_filepath):
            msg = 'No MV grid file for MV grid {}'.format(mv_grid_id)
            logger.error(msg)
            raise Exception(msg)

        # Initalize eDisGo with this MV grid
        logger.info(("MV grid {}: Initialize MV grid").format(mv_grid_id))

        edisgo_grid = EDisGo(ding0_grid=ding0_filepath,
                             worst_case_analysis='worst-case')

        logger.info(("MV grid {}: Changing eDisGo's voltage configurations "
                     + "for initial reinforcement").format(mv_grid_id))

        edisgo_grid.network.config[
            'grid_expansion_allowed_voltage_deviations'] = {
            'hv_mv_trafo_offset': 0.04,
                'hv_mv_trafo_control_deviation': 0.0,
                'mv_load_case_max_v_deviation': 0.055,
                'mv_feedin_case_max_v_deviation': 0.02,
                'lv_load_case_max_v_deviation': 0.065,
                'lv_feedin_case_max_v_deviation': 0.03,
                'mv_lv_station_load_case_max_v_deviation': 0.02,
                'mv_lv_station_feedin_case_max_v_deviation': 0.01
        }

        # Inital grid reinforcements
        logger.info(("MV grid {}: Initial MV grid reinforcement "
                     + "(worst-case anaylsis)").format(mv_grid_id))

        edisgo_grid.reinforce()

        # Get costs for initial reinforcement
        # TODO: Implement a separate cost function
        costs_grouped = \
            edisgo_grid.network.results.grid_expansion_costs.groupby(
                ['type']).sum()
        costs = pd.DataFrame(
            costs_grouped.values,
            columns=costs_grouped.columns,
            index=[[edisgo_grid.network.id] * len(costs_grouped),
                   costs_grouped.index]).reset_index()
        costs.rename(columns={'level_0': 'grid'}, inplace=True)

        costs_before = costs

        total_costs_before_EUR = costs_before['total_costs'].sum() * 1000
        logger.info(
            ("MV grid {}: Costs for initial "
             + "reinforcement: EUR {}").format(
                mv_grid_id,
                "{0:,.2f}".format(total_costs_before_EUR)))

        logger.info((
            "MV grid {}: Resetting grid after initial reinforcement"
        ).format(mv_grid_id))
        edisgo_grid.network.results = Results(edisgo_grid.network)
        # Reload the (original) eDisGo configs
        edisgo_grid.network.config = None

        # eTraGo case begins here
        logger.info("MV grid {}: eTraGo feed-in case".format(mv_grid_id))

        # Update eDisGo settings (from config files) with scenario settings
        logger.info("MV grid {}: Updating eDisgo configuration".format(
            mv_grid_id))
        # Update configs with eGo's scenario settings
        self._update_edisgo_configs(edisgo_grid)

        # Generator import for NEP 2035 and eGo 100 scenarios
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

        # Time Series from eTraGo
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

        # Curtailment
        if apply_curtailment:
            logger.info('Including Curtailment')

            gens_df = tools.get_gen_info(edisgo_grid.network)
            solar_wind_capacities = gens_df.groupby(
                by=['type', 'weather_cell_id']
            )['nominal_capacity'].sum()

            curt_cols = [
                i for i in specs['ren_curtailment'].columns
                if i in solar_wind_capacities.index
            ]

            if not curt_cols:
                raise ImportError(
                    ("MV grid {}: Data doesn't match").format(mv_grid_id))

            curt_abs = pd.DataFrame(
                columns=pd.MultiIndex.from_tuples(curt_cols))

            for col in curt_abs:
                curt_abs[col] = (
                    specs['ren_curtailment'][col]
                    * solar_wind_capacities[col])

            edisgo_grid.curtail(
                curtailment_timeseries=curt_abs,
                methodology='voltage-based',
                solver=self._solver,
                voltage_threshold=self._curtailment_voltage_threshold)
        else:
            logger.info('No curtailment applied')

        # Storage Integration
        costs_without_storage = None
        if storage_integration:
            if self._ext_storage:
                if not specs['battery_p_series'] is None:
                    logger.info('Integrating storages in MV grid')
                    edisgo_grid.integrate_storage(
                        timeseries=specs['battery_p_series'],
                        position='distribute_storages_mv',
                        timeseries_reactive_power=specs[
                            'battery_q_series'
                        ])  # None if no pf_post_lopf
                    costs_without_storage = (
                        edisgo_grid.network.results.storages_costs_reduction[
                            'grid_expansion_costs_initial'].values[0])
        else:
            logger.info('No storage integration')

        logger.info("MV grid {}: eDisGo grid analysis".format(mv_grid_id))

        edisgo_grid.reinforce(timesteps_pfa=self._timesteps_pfa)

        if costs_without_storage is not None:
            costs_with_storage = (
                edisgo_grid.network.results.grid_expansion_costs[
                    'total_costs'].sum())
            if costs_with_storage >= costs_without_storage:
                logger.warning(
                    "Storage did not benefit MV grid {}".format(
                        mv_grid_id))
                st = edisgo_grid.network.mv_grid.graph.nodes_by_attribute(
                    'storage')
                for storage in st:
                    tools.disconnect_storage(edisgo_grid.network, storage)

        self._status_update(mv_grid_id, 'end')

        path = os.path.join(self._results, str(mv_grid_id))
        edisgo_grid.network.results.save(path)

        return {edisgo_grid.network.id: path}

    def _save_edisgo_results(self):

        if not os.path.exists(self._results):
            os.makedirs(self._results)

        with open(
                os.path.join(self._results, 'edisgo_args.json'),
                'w') as fp:
            json.dump(self._edisgo_args, fp)

        self._grid_choice.to_csv(self._results + '/grid_choice.csv')

    def _laod_edisgo_results(self):

        # Load the grid choice form CSV
        self._grid_choice = pd.read_csv(
            os.path.join(self._csv_import, 'grid_choice.csv'),
            index_col=0)
        self._grid_choice['represented_grids'] = self._grid_choice.apply(
            lambda x: eval(x['represented_grids']), axis=1)

        for idx, row in self._grid_choice.iterrows():
            mv_grid_id = int(row['the_selected_network_id'])

            try:
                # Grid expansion costs
                file_path = os.path.join(
                    self._csv_import,
                    str(mv_grid_id),
                    'grid_expansion_results',
                    'grid_expansion_costs.csv')

                grid_expansion_costs = pd.read_csv(
                    file_path,
                    index_col=0)

                # powerflow results
                pf_path = os.path.join(
                    self._csv_import,
                    str(mv_grid_id),
                    'powerflow_results',
                    'apparent_powers.csv')

                s_res = pd.read_csv(
                    pf_path,
                    index_col=0,
                    parse_dates=True)

                # Configs
                config_path = os.path.join(
                    self._csv_import,
                    str(mv_grid_id),
                    'configs.csv')

                edisgo_config = {}
                with open(config_path, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        a = iter(row[1:])
                        edisgo_config[row[0]] = dict(zip(a, a))

                # PyPSA network
                pypsa_path = os.path.join(
                    self._csv_import,
                    str(mv_grid_id),
                    'pypsa_network')

                imported_pypsa = pypsa.Network()
                imported_pypsa.import_from_csv_folder(pypsa_path)

                # Storages
                storage_path = os.path.join(
                    self._csv_import,
                    str(mv_grid_id),
                    'storage_integration_results',
                    'storages.csv')

                if os.path.exists(storage_path):
                    storages = pd.read_csv(
                        storage_path,
                        index_col=0)
                else:
                    storages = pd.DataFrame(
                        columns=['nominal_power', 'voltage_level'])

                edisgo_grid = _EDisGoImported(
                    grid_expansion_costs,
                    s_res,
                    storages,
                    imported_pypsa,
                    edisgo_config)

                self._edisgo_grids[
                    mv_grid_id
                ] = edisgo_grid

                logger.info("Imported MV grid {}".format(mv_grid_id))
            except:
                self._edisgo_grids[
                    mv_grid_id
                ] = "This grid failed to reimport"

                logger.warning(
                    "MV grid {} could not be loaded".format(mv_grid_id))

    def _get_mv_grid_from_bus_id(self, session, bus_id):
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
            subst_id = session.query(
                ormclass_hvmv_subst.subst_id
            ).filter(
                ormclass_hvmv_subst.otg_id == bus_id,
                ormclass_hvmv_subst.version == self._grid_version
            ).scalar()

        if self._versioned is False:
            ormclass_hvmv_subst = model_draft.__getattribute__(
                'EgoGridHvmvSubstation'
            )
            subst_id = session.query(
                ormclass_hvmv_subst.subst_id
            ).filter(
                ormclass_hvmv_subst.otg_id == bus_id
            ).scalar()

        return subst_id

    def _get_bus_id_from_mv_grid(self, session, subst_id):
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
            bus_id = session.query(
                ormclass_hvmv_subst.otg_id
            ).filter(
                ormclass_hvmv_subst.subst_id == subst_id,
                ormclass_hvmv_subst.version == self._grid_version
            ).scalar()

        if self._versioned is False:
            ormclass_hvmv_subst = model_draft.__getattribute__(
                'EgoGridHvmvSubstation'
            )
            bus_id = session.query(
                ormclass_hvmv_subst.otg_id
            ).filter(
                ormclass_hvmv_subst.subst_id == subst_id
            ).scalar()

        return bus_id


class _ETraGoData:
    """
    Container for minimal eTraGo network. This minimal network is required
    for the parallelization of eDisGo.

    """

    def __init__(self, etrago_network):

        self.snapshots = getattr(
            etrago_network, "snapshots")
        self.storage_units = getattr(
            etrago_network, "storage_units")
        self.storage_units_t = getattr(
            etrago_network, "storage_units_t")
        self.generators = getattr(
            etrago_network, "generators")
        self.generators_t = getattr(
            etrago_network, "generators_t")


class _EDisGoImported:
    """
    Imported (reduced) eDisGo class.
    This class allows the import reduction to only the attributes used in eGo
    """

    def __init__(
            self,
            grid_expansion_costs,
            s_res,
            storages,
            pypsa,
            edisgo_config):

        self.network = _NetworkImported(
            grid_expansion_costs,
            s_res,
            storages,
            pypsa,
            edisgo_config)


class _NetworkImported:
    """
    Reduced eDisG network class, used of eGo's reimport
    """

    def __init__(
            self,
            grid_expansion_costs,
            s_res,
            storages,
            pypsa,
            edisgo_config):

        self.results = _ResultsImported(
            grid_expansion_costs,
            s_res,
            storages)

        self.pypsa = pypsa
        self.config = edisgo_config


class _ResultsImported:
    """
    Reduced eDisG results class, used of eGo's reimport
    """

    def __init__(
            self,
            grid_expansion_costs,
            s_res,
            storages):

        self.grid_expansion_costs = grid_expansion_costs
        self.storages = storages
        self._s_res = s_res

    def s_res(self):
        return self._s_res


def parallelizer(
        ding0_id_list,
        func,
        func_arguments,
        max_calc_time,
        workers=mp2.cpu_count(),
        worker_lifetime=1):
    """
    Use python multiprocessing toolbox for parallelization

    Several grids are analyzed in parallel based on your custom function that
    defines the specific application of eDisGo.

    Parameters
    ----------
    ding0_id_list : list of int
        List of ding0 grid data IDs (also known as HV/MV substation IDs)
    func : any function
        Your custom function that shall be parallelized
    func_arguments : tuple
        Arguments to custom function ``func``
    workers: int
        Number of parallel process
    worker_lifetime : int
        Bunch of grids sequentially analyzed by a worker

    Notes
    -----
    Please note, the following requirements for the custom function which is to
    be executed in parallel

    #. It must return an instance of the type :class:`~.edisgo.EDisGo`.
    #. The first positional argument is the MV grid district id (as int). It is
       prepended to the tuple of arguments ``func_arguments``


    Returns
    -------
    containers : dict of :class:`~.edisgo.EDisGo`
        Dict of EDisGo instances keyed by its ID
    """
    def collect_pool_results(result):
        """
        Store results from parallelized calculation in structured manner

        Parameters
        ----------
        result: :class:`~.edisgo.EDisGo`
        """
        results.update(result)

    def error_callback(key):

        #        message='Failed'
        #        func_arguments[0]._status_update(key, 'end', message)
        return lambda o: results.update({key: o})

    results = {}
    max_calc_time_seconds = max_calc_time * 3600

    def initializer():
        import pickle
        pickle.DEFAULT_PROTOCOL = 4
        import dill
        dill.settings['protocol'] = 4

    pool = mp2.Pool(
        workers,
        initializer=initializer,
        maxtasksperchild=worker_lifetime)

    result_objects = {}
    for ding0_id in ding0_id_list:
        edisgo_args = (ding0_id, *func_arguments)

        result_objects[ding0_id] = pool.apply_async(
            func=func,
            args=edisgo_args,
            callback=collect_pool_results,
            error_callback=error_callback(ding0_id))

    errors = {}
    successes = {}
    start = datetime.now()
    end = (start + td(hours=max_calc_time)).isoformat(' ')
    logger.info(
        "Jobs started. They will time out at {}."
        .format(end[:end.index('.')]))
    current = datetime.now()
    time_spent = 0
    while (result_objects and
            ((current - start).seconds <= max_calc_time_seconds)):
        done = []
        tick = (current - start).seconds * 100 / max_calc_time_seconds
        if tick - time_spent >= 1 or tick > 100:
            hours_to_go = (current - start).seconds / 3600
            logger.info("{:.2f}% ({:.2f}/{}h) spent"
                        .format(tick, hours_to_go, max_calc_time))
            logger.info("Jobs time out in {:.2f}h."
                        .format(max_calc_time - hours_to_go))
            time_spent = tick
        for grid, result in result_objects.items():
            if result.ready():
                logger.info(
                    "MV grid {} ready. Trying to `get` the result."
                    .format(grid))
                done.append(grid)
                if not result.successful():
                    try:
                        # We already know that this was not successful, so the
                        # `get` is only here to re-raise the exception that
                        # occurred.
                        result.get()
                    except Exception as e:
                        logger.warning(
                            "MV grid {} failed due to {e!r}: '{e}'."
                            .format(grid, e=e))
                        errors[grid] = e
                else:
                    logger.info(
                        "MV grid {} calculated successfully.".format(grid))
                    successes[grid] = result.get()
                logger.info(
                    "Done `get`ting the result for MV grid {}."
                    .format(grid))
        for grid in done:
            del result_objects[grid]
        sleep(1)
        current = datetime.now()

    # Now we know that we either reached the timeout, (x)or that all
    # calculations are done. We just have collect what exactly is the case.
    # This is done by `get`ting the results with a timeout of 0. If any of them
    # are not yet done, a `TimeoutError` will be triggered, which we can
    # collect like all other errors.
    if not result_objects:
        logger.info("All MV grids stopped before the timeout.")
    else:
        logger.warning("Some MV grid simulations timed out.")
        pool.terminate()

    end = datetime.now()
    delta = end - start
    logger.info("Execution finished after {:.2f} hours".format(
        delta.seconds / 3600))

    done = []
    for grid, result in result_objects.items():
        done.append(grid)
        try:
            successes[grid] = result.get(timeout=0)
            logger.info("MV grid {} calculated successfully.".format(grid))
        except Exception as e:
            logger.warning(
                "MV grid {} failed due to {e!r}: '{e}'.".format(grid, e=e))
            errors[grid] = e
    for grid in done:
        del result_objects[grid]

    if errors:
        logger.info("MV grid calculation error details:")
        for grid, error in errors.items():
            logger.info("  {}".format(grid))
            strings = TracebackException.from_exception(error).format()
            lines = [line for string in strings for line in string.split("\n")]
            for line in lines:
                logger.info("    " + line)

    pool.close()
    pool.join()

    return results
