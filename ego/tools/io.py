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
"""This file contains the eGo main class as well as input & output functions
of eGo in order to build the eGo application container.
"""
import sys
import os
import json
import logging
logger = logging.getLogger('ego')
import pandas as pd
import numpy as np
import json

if not 'READTHEDOCS' in os.environ:
    import pyproj as proj
    from shapely.geometry import Polygon, Point, MultiPolygon
    from sqlalchemy import MetaData, create_engine,  and_, func
    from sqlalchemy.orm import sessionmaker
    import oedialect
    from geoalchemy2 import *

    from egoio.tools import db
    from etrago.tools.io import load_config_file
    from egoio.db_tables.model_draft import EgoGridPfHvSource as Source,\
        EgoGridPfHvTempResolution as TempResolution
    from ego.tools.results import (create_etrago_results)
    from ego.tools.storages import (etrago_storages_investment, etrago_storages)
    from ego.tools.economics import (
        etrago_operating_costs,
        etrago_grid_investment,
        get_generator_investment,
        etrago_convert_overnight_cost)
    from ego.tools.utilities import (get_scenario_setting,
                                     get_time_steps, fix_leading_separator)
    from ego.tools.edisgo_integration import EDisGoNetworks
    from egoio.db_tables.model_draft import RenpassGisParameterRegion
    from egoio.db_tables import model_draft, grid
    from etrago.tools.plot import (plot_line_loading, plot_stacked_gen,
                                   curtailment, gen_dist, storage_distribution,
                                   plot_voltage, plot_residual_load,
                                   plot_line_loading_diff, full_load_hours,
                                   nodal_gen_dispatch, plot_q_flows,
                                   max_load, storage_expansion,
                                   nodal_production_balance, gen_dist_diff)
    from etrago.appl import etrago
    from importlib import import_module
    import pypsa
    import re
    from ego.tools.plots import (plot_grid_storage_investment,
                                 power_price_plot, plot_storage_use, igeoplot,
                                 plot_edisgo_cluster,
                                 plot_line_expansion,
                                 plot_storage_expansion)

__copyright__ = ("Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc"


class egoBasic(object):
    """The eGo basic class select and creates based on your
    ``scenario_setting.json`` file  your definded eTraGo and
    eDisGo results container. And contains the session for the
    database connection.

    Parameters
    ----------
    jsonpath : :obj:`json`
        Path to ``scenario_setting.json`` file.

    Returns
    -------
    json_file : :obj:dict
        Dictionary of the ``scenario_setting.json`` file
    session : :sqlalchemy:`sqlalchemy.orm.session.Session<orm/session_basics.html>`
        SQLAlchemy session to the OEDB

    """

    def __init__(self, *args, **kwargs):
        """
        """

        logger.info("Using scenario setting: {}".format(self.jsonpath))

        self.json_file = None
        self.session = None
        self.scn_name = None

        self.json_file = get_scenario_setting(jsonpath=self.jsonpath)

        # Database connection from json_file
        try:
            conn = db.connection(section=self.json_file['eTraGo']['db'])
            Session = sessionmaker(bind=conn)
            self.session = Session()
            logger.info('Connected to Database')
        except:
            logger.error('Failed connection to Database',  exc_info=True)

        # get scn_name
        self.scn_name = self.json_file['eTraGo']['scn_name']


class eTraGoResults(egoBasic):
    """The ``eTraGoResults`` class creates and contains all results
    of eTraGo  and it's network container for eGo.

    Returns
    -------
    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :func:`etrago.appl.etrago`
    etrago: :pandas:`pandas.Dataframe<dataframe>`
        DataFrame which collects several eTraGo results
    """

    def __init__(self, *args, **kwargs):
        """
        """
        super(eTraGoResults, self).__init__(self, *args, **kwargs)
        self.etrago = None
        self._etrago_network = None
        self._etrago_disaggregated_network = None

        logger.info('eTraGo section started')

        if self.json_file['eGo']['result_id'] != None:

            # Delete arguments from scenario_setting
            logger.info('Remove given eTraGo settings from scenario_setting')

            try:
                self.json_file['eGo']['eTraGo'] = False

                for key in self.json_file['eTraGo'].keys():

                    self.json_file['eTraGo'][key] = 'removed by DB recover'

                # ToDo add scenario_setting for results
                self.json_file['eTraGo']['db'] = self.json_file['eTraGo']['db']
                logger.info(
                    'Add eTraGo scenario_setting from oedb result')
                # To do ....
                _prefix = 'EgoGridPfHvResult'
                schema = 'model_draft'
                packagename = 'egoio.db_tables'
                _pkg = import_module(packagename + '.' + schema)

                # get metadata
                orm_meta = getattr(_pkg, _prefix + 'Meta')
                self.jsonpath = recover_resultsettings(self.session,
                                                       self.json_file,
                                                       orm_meta,
                                                       self.json_file['eGo']
                                                       ['result_id'])

                # add etrago_disaggregated_network from DB
                logger.info(
                    "Recovered eTraGo network uses kmeans: {}".format(
                        self.json_file['eTraGo']['network_clustering_kmeans']))

            except KeyError:
                pass

            logger.info('Create eTraGo network from oedb result')
            self._etrago_network = etrago_from_oedb(
                self.session, self.json_file)

            if self.json_file['eTraGo']['disaggregation'] != False:
                self._etrago_disaggregated_network = self._etrago_network
            else:
                logger.warning('No disaggregated network found in DB')
                self._etrago_disaggregated_network = None

        # create eTraGo NetworkScenario
        if self.json_file['eGo']['eTraGo'] is True:

            if self.json_file['eGo'].get('csv_import_eTraGo') != False:

                logger.info('Caution, import disaggregation '
                            'data of former Cluster')

                # get pathway
                pathway = self.json_file['eGo'].get('csv_import_eTraGo')

                try:
                    # create Network from csv
                    self._etrago_network = pypsa.Network()
                    self._etrago_network.import_from_csv_folder(pathway)
                    logger.info('Create eTraGo network from CSV result')

                    # get disaggregation
                    self._etrago_disaggregated_network = pypsa.Network()
                    self._etrago_disaggregated_network.\
                        import_from_csv_folder(pathway+'/disaggregated')
                    logger.info('Create eTraGo disaggregated network '
                                'from CSV result')

                except TypeError:
                    file_path = "disaggregated/network.csv"
                    fix_leading_separator(pathway+"/"+file_path)

                    file_path = "network.csv"
                    fix_leading_separator(pathway+"/"+file_path)

                    self._etrago_network = pypsa.Network()
                    self._etrago_network.import_from_csv_folder(pathway)
                    logger.info('Create eTraGo network from CSV result')

                    # get disaggregation
                    self._etrago_disaggregated_network = pypsa.Network()
                    self._etrago_disaggregated_network.\
                        import_from_csv_folder(pathway+'/disaggregated')
                    logger.info('Create eTraGo disaggregated network'
                                'from CSV result')

                args_name = "args.json"
                with open(pathway+'/'+args_name) as f:
                    etrago_args = json.load(f)
                    logger.info('Using argument file')

                    if etrago_args.get('extendable') == ['network', 'storages']:
                        etrago_args.update(
                            {'extendable': ['network', 'storage']})
                        logger.info(
                            'Changed naming of storages to storage of args')

                    if etrago_args.get('extendable') == ['storages']:
                        etrago_args.update({'extendable': ['storage']})
                        logger.info(
                            'Changed naming of storages to storage of args')

                    for key in self.json_file['eTraGo'].keys():
                        try:
                            self.json_file['eTraGo'][key] = etrago_args[key]
                        except KeyError:
                            pass

            else:
                logger.info('Create eTraGo network calcualted by eGo')

                if self.json_file['eTraGo']['disaggregation'] != False:

                    etrago_network, etrago_disaggregated_network = etrago(
                        self.json_file['eTraGo'])

                    self._etrago_network = etrago_network
                    self._etrago_disaggregated_network = (
                        etrago_disaggregated_network)
                else:
                    logger.warning("Only one network is used.")

                    etrago_network, etrago_disaggregated_network = etrago(
                        self.json_file['eTraGo'])

                    self._etrago_network = etrago_network
                    self._etrago_disaggregated_network = (
                        etrago_disaggregated_network)

        # Add selected results to results container
        # -----------------------------------------

        self.etrago = pd.DataFrame()
        self.etrago.network = self._etrago_network
        self.etrago.disaggregated_network = self._etrago_disaggregated_network

        # Add function
        self.etrago.storage_investment_costs = etrago_storages_investment(
            self.etrago.network, self.json_file, self.session)
        self.etrago.storage_charges = etrago_storages(self.etrago.network)

        self.etrago.operating_costs = etrago_operating_costs(
            self.etrago.network)
        self.etrago.generator = create_etrago_results(self.etrago.network,
                                                      self.scn_name)
        self.etrago.grid_investment_costs = \
            etrago_grid_investment(self.etrago.network,
                                   self.json_file, self.session)

        # add functions direct
        # self._etrago_network.etrago_line_loading = etrago_line_loading
        self.etrago.plot_line_loading = self._line_loading
        self.etrago.plot_stacked_gen = self._stacked_gen
        self.etrago.plot_curtailment = self._curtailment
        self.etrago.plot_gen_dist = self._gen_dist
        self.etrago.plot_storage_distribution = self._storage_distribution
        self.etrago.plot_line_loading_diff = self._line_loading_diff
        self.etrago.plot_residual_load = self._residual_load
        self.etrago.plot_voltage = self._voltage
        self.etrago.plot_nodal_gen_dispatch = \
            self._nodal_gen_dispatch
        self.etrago.plot_full_load_hours = self._full_load_hours
        self.etrago.plot_q_flows = self._plot_q_flows
        self.etrago.plot_max_load = self._max_load
        self.etrago.plot_storage_expansion = self._storage_expansion
        self.etrago.plot_nodal_production_balance = (
            self._nodal_production_balance)
        self.etrago.plot_gen_dist_diff = self._gen_dist_diff

    if not 'READTHEDOCS' in os.environ:
        # include eTraGo functions and methods
        def _gen_dist_diff(self, **kwargs):
            """
            Integrate and use function from eTraGo.
            For more information see:
            """

            return gen_dist_diff(networkA=self.etrago.network,
                                 **kwargs)

        def _nodal_production_balance(self, **kwargs):
            """
            Integrate and use function from eTraGo.
            For more information see:
            """

            return nodal_production_balance(network=self.etrago.network,
                                            **kwargs)

        def _storage_expansion(self, **kwargs):
            """
            Integrate and use function from eTraGo.
            For more information see:
            """

            return storage_expansion(network=self.etrago.network,
                                     **kwargs)

        def _max_load(self, **kwargs):
            """
            Integrate and use function from eTraGo.
            For more information see:
            """

            return max_load(network=self.etrago.network,
                            **kwargs)

        def _plot_q_flows(self):
            """
            Integrate and use function from eTraGo.
            For more information see:
            """

            return plot_q_flows(network=self.etrago.network)

        def _line_loading(self, **kwargs):
            """
            Integrate and use function from eTraGo.
            For more information see:
            """
            # add if time_step <1  -> plot
            return plot_line_loading(network=self.etrago.network, **kwargs)

        def _stacked_gen(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return plot_stacked_gen(network=self.etrago.network, **kwargs)

        def _curtailment(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return curtailment(network=self.etrago.network, **kwargs)

        def _gen_dist(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return gen_dist(network=self.etrago.network, **kwargs)

        def _storage_distribution(self, scaling=1, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return storage_distribution(network=self.etrago.network,
                                        scaling=1, **kwargs)

        def _voltage(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return plot_voltage(network=self.etrago.network, **kwargs)

        def _residual_load(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return plot_residual_load(network=self.etrago.network, **kwargs)

        def _line_loading_diff(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return plot_line_loading_diff(networkA=self.etrago.network,
                                          **kwargs)

        def _nodal_gen_dispatch(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return nodal_gen_dispatch(network=self.etrago.network,
                                      **kwargs)

        def _full_load_hours(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return full_load_hours(network=self.etrago.network, **kwargs)


class eDisGoResults(eTraGoResults):
    """The ``eDisGoResults`` class create and contains all results
    of eDisGo and its network containers.

    """

    def __init__(self, *args, **kwargs):
        super(eDisGoResults, self).__init__(self, *args, **kwargs)

        if self.json_file['eGo']['eDisGo'] is True:
            logger.info('Create eDisGo network')

            self._edisgo = EDisGoNetworks(
                json_file=self.json_file,
                etrago_network=self.etrago.disaggregated_network)
        else:
            self._edisgo = None
            logger.info('No eDisGo network')

    @property
    def edisgo(self):
        """
        Contains basic informations about eDisGo

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`

        """
        return self._edisgo


class eGo(eDisGoResults):
    """Main eGo module which includs all results and main functionalities.


    Returns
    -------
    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    edisgo.network : :class:`ego.tools.edisgo_integration.EDisGoNetworks`
        Contains multiple eDisGo networks
    edisgo : :pandas:`pandas.Dataframe<dataframe>`
        aggregated results of eDisGo
    etrago : :pandas:`pandas.Dataframe<dataframe>`
        aggregated results of eTraGo


    """

    def __init__(self, jsonpath, *args, **kwargs):
        self.jsonpath = jsonpath
        super(eGo, self).__init__(self,  *args, **kwargs)

        # add total results here
        self._total_investment_costs = None
        self._total_operation_costs = None
        self._calculate_investment_cost()
        self._storage_costs = None
        self._ehv_grid_costs = None
        self._mv_grid_costs = None

    def _calculate_investment_cost(
            self,
            storage_mv_integration=True):
        """ Get total investment costs of all voltage level for storages
        and grid expansion
        """

        self._total_inv_cost = pd.DataFrame(columns=['component',
                                                     'voltage_level',
                                                     'capital_cost'
                                                     ])
        _grid_ehv = None
        if 'network' in self.json_file['eTraGo']['extendable']:
            _grid_ehv = self.etrago.grid_investment_costs
            _grid_ehv['component'] = 'grid'

            self._total_inv_cost = self._total_inv_cost.\
                append(_grid_ehv, ignore_index=True)

        _storage = None
        if 'storage' in self.json_file['eTraGo']['extendable']:
            _storage = self.etrago.storage_investment_costs
            _storage['component'] = 'storage'

            self._total_inv_cost = self._total_inv_cost.\
                append(_storage, ignore_index=True)

        _grid_mv_lv = None
        if self.json_file['eGo']['eDisGo'] is True:

            _grid_mv_lv = self.edisgo.grid_investment_costs
            if _grid_mv_lv is not None:
                _grid_mv_lv['component'] = 'grid'
                _grid_mv_lv['differentiation'] = 'domestic'

                self._total_inv_cost = self._total_inv_cost.\
                    append(_grid_mv_lv, ignore_index=True)

        # add overnight costs
        self._total_investment_costs = self._total_inv_cost
        self._total_investment_costs[
            'overnight_costs'] = etrago_convert_overnight_cost(
            self._total_investment_costs['capital_cost'], self.json_file)

        # Include MV storages into the _total_investment_costs dataframe
        if storage_mv_integration is True:
            if _grid_mv_lv is not None:
                self._integrate_mv_storage_investment()

        # sort values
        self._total_investment_costs['voltage_level'] = pd.Categorical(
            self._total_investment_costs['voltage_level'], ['ehv', 'hv', 'mv',
                                                            'lv', 'mv/lv'])
        self._total_investment_costs = (
            self._total_investment_costs.sort_values('voltage_level'))

        self._storage_costs = _storage
        self._ehv_grid_costs = _grid_ehv
        self._mv_grid_costs = _grid_mv_lv

    def _integrate_mv_storage_investment(self):
        """
        Updates the total investment costs dataframe and includes the
        storage integrated in MV grids.
        """

        costs_df = self._total_investment_costs

        total_stor = self._calculate_all_extended_storages()
        mv_stor = self._calculate_mv_storage()

        integrated_share = mv_stor / total_stor

        try:

            if integrated_share > 0:

                ehv_stor_idx = costs_df.index[
                    (costs_df['component'] == 'storage')
                    & (costs_df['voltage_level'] == 'ehv')][0]

                int_capital_costs = costs_df.loc[ehv_stor_idx][
                    'capital_cost'
                ] * integrated_share
                int_overnight_costs = costs_df.loc[ehv_stor_idx][
                    'overnight_costs'
                ] * integrated_share

                costs_df.at[
                    ehv_stor_idx,
                    'capital_cost'
                ] = (
                    costs_df.loc[ehv_stor_idx]['capital_cost']
                    - int_capital_costs)

                costs_df.at[
                    ehv_stor_idx,
                    'overnight_costs'
                ] = (
                    costs_df.loc[ehv_stor_idx]['overnight_costs']
                    - int_overnight_costs)

                new_storage_row = {
                    'component': ['storage'],
                    'voltage_level': ['mv'],
                    'differentiation': ['domestic'],
                    'capital_cost': [int_capital_costs],
                    'overnight_costs': [int_overnight_costs]}

                new_storage_row = pd.DataFrame(new_storage_row)
                costs_df = costs_df.append(new_storage_row)

                self._total_investment_costs = costs_df
        except:
            logger.info(
                'Something went wrong with the MV storage distribution.')

    def _calculate_all_extended_storages(self):
        """
        Returns the all extended storage p_nom_opt in MW.
        """
        etrago_network = self._etrago_disaggregated_network

        stor_df = etrago_network.storage_units.loc[
            (etrago_network.storage_units['p_nom_extendable'] == True)]

        stor_df = stor_df[['bus', 'p_nom_opt']]

        all_extended_storages = stor_df['p_nom_opt'].sum()

        return all_extended_storages

    def _calculate_mv_storage(self):
        """
        Returns the storage p_nom_opt in MW, integrated in MV grids
        """
        etrago_network = self._etrago_disaggregated_network

        min_extended = 0.3
        stor_df = etrago_network.storage_units.loc[
            (etrago_network.storage_units['p_nom_extendable'] == True)
            & (etrago_network.storage_units['p_nom_opt'] > min_extended)
            & (etrago_network.storage_units['max_hours'] <= 20.)]

        stor_df = stor_df[['bus', 'p_nom_opt']]

        integrated_storage = .0  # Storage integrated in MV grids

        for idx, row in stor_df.iterrows():
            bus_id = row['bus']
            p_nom_opt = row['p_nom_opt']

            mv_grid_id = self.edisgo.get_mv_grid_from_bus_id(bus_id)

            if not mv_grid_id:
                continue

            logger.info("Checking storage integration for MV grid {}".format(
                mv_grid_id))

            grid_choice = self.edisgo.grid_choice

            cluster = grid_choice.loc[
                [mv_grid_id in repr_grids for repr_grids in grid_choice[
                    'represented_grids']]]

            if len(cluster) == 0:
                continue

            else:
                representative_grid = cluster[
                    'the_selected_network_id'].values[0]

            if hasattr(self.edisgo.network[representative_grid], 'network'):
                integration_df = self.edisgo.network[
                    representative_grid].network.results.storages

                integrated_power = integration_df['nominal_power'].sum() / 1000
            else:
                integrated_power = 0.

            if integrated_power > p_nom_opt:
                integrated_power = p_nom_opt

            integrated_storage = integrated_storage + integrated_power

        return integrated_storage

    @property
    def total_investment_costs(self):
        """
        Contains all investment informations about eGo

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`

        """

        return self._total_investment_costs

    @property
    def total_operation_costs(self):
        """
        Contains all operation costs information about eGo

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`

        """
        self._total_operation_costs = self.etrago.operating_costs
        # append eDisGo

        return self._total_operation_costs

    def plot_total_investment_costs(self,
                                    filename=None,
                                    display=False, **kwargs):
        """ Plot total investment costs
        """

        if filename is None:
            filename = "results/plot_total_investment_costs.pdf"
            display = True

        return plot_grid_storage_investment(
            self._total_investment_costs,
            filename=filename,
            display=display,
            **kwargs)

    def plot_power_price(self, filename=None, display=False):
        """ Plot power prices per carrier of calculation
        """
        if filename is None:
            filename = "results/plot_power_price.pdf"
            display = True

        return power_price_plot(self, filename=filename, display=display)

    def plot_storage_usage(self, filename=None, display=False):
        """ Plot storage usage by charge and discharge
        """
        if filename is None:
            filename = "results/plot_storage_usage.pdf"
            display = True

        return plot_storage_use(self, filename=filename, display=display)

    def plot_edisgo_cluster(self, filename=None, display=False,
                            **kwargs):
        """ Plot the Clustering of selected Dingo networks
        """
        if filename is None:
            filename = "results/plot_edisgo_cluster.pdf"
            display = True

        return plot_edisgo_cluster(self, filename=filename, display=display,
                                   **kwargs)

    def plot_line_expansion(self, **kwargs):
        """Plot line expantion per line
        """

        return plot_line_expansion(self, **kwargs)

    def plot_storage_expansion(self, **kwargs):
        """Plot storage expantion per bus
        """

        return plot_storage_expansion(self, **kwargs)

    @property
    def iplot(self):
        """ Get iplot of results as html
        """
        return igeoplot(self)

    # write_results_to_db():
    logging.info('Initialisation of eGo Results')


def results_to_excel(ego):
    """
    Wirte results of ego.total_investment_costs to an excel file
    """
    # Write the results as xlsx file
    # ToDo add time of calculation to file name
    # add xlsxwriter to setup
    writer = pd.ExcelWriter('open_ego_results.xlsx', engine='xlsxwriter')

    # write results of installed Capacity by fuels
    ego.total_investment_costs.to_excel(writer,
                                        index=False,
                                        sheet_name='Total Calculation')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    # buses


def etrago_from_oedb(session, json_file):
    """Function which import eTraGo results for the Database by the
    ``result_id`` number.

    Parameters
    ----------
    session : :sqlalchemy:`sqlalchemy.orm.session.Session<orm/session_basics.html>`
        SQLAlchemy session to the OEDB
    json_file : :obj:`dict`
        Dictionary of the ``scenario_setting.json`` file

    Returns
    -------
    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`

    """

    result_id = json_file['eGo']['result_id']

    # functions
    def map_ormclass(name):
        """
        Function to map sqlalchemy classes
        """
        try:
            _mapped[name] = getattr(_pkg, _prefix + name)

        except AttributeError:
            logger.warning('Relation %s does not exist.' % name)

        return _mapped

    def id_to_source(query):

        # ormclass = map_ormclass(name)
        # query = session.query(ormclass).filter(ormclass.result_id == result_id)

        # TODO column naming in database
        return {k.source_id: k.name for k in query.all()}

    def dataframe_results(name, session, result_id, ormclass):
        """
        Function to get pandas DataFrames by the result_id

        Parameters
        ----------
        session : :sqlalchemy:`sqlalchemy.orm.session.Session<orm/session_basics.html>`
            SQLAlchemy session to the OEDB
        """

        query = session.query(ormclass).filter(ormclass.result_id == result_id)

        if name == 'Transformer':
            name = 'Trafo'

        df = pd.read_sql(query.statement,
                         session.bind,
                         index_col=name.lower() + '_id')

        if name == 'Link':
            df['bus0'] = df.bus0.astype(int)
            df['bus1'] = df.bus1.astype(int)

        if 'source' in df:

            source_orm = Source

            source_query = session.query(source_orm)

            df.source = df.source.map(id_to_source(source_query))

        if str(ormclass)[:-2].endswith('T'):
            df = pd.Dataframe()

        return df

    def series_results(name, column, session, result_id, ormclass):
        """
        Function to get Time Series as pandas DataFrames by the result_id

        Parameters
        ----------
        session: : sqlalchemy: `sqlalchemy.orm.session.Session < orm/session_basics.html >`
            SQLAlchemy session to the OEDB
        """

        # TODO - check index of bus_t and soon is wrong!
        # TODO: pls make more robust

        id_column = re.findall(r'[A-Z][^A-Z]*', name)[0] + '_' + 'id'
        id_column = id_column.lower()

        query = session.query(
            getattr(ormclass, id_column),
            getattr(ormclass, column).
            label(column)).filter(and_(
                ormclass.result_id == result_id
            ))

        df = pd.io.sql.read_sql(query.statement,
                                session.bind,
                                columns=[column],
                                index_col=id_column)

        df.index = df.index.astype(str)

        # change of format to fit pypsa
        df = df[column].apply(pd.Series).transpose()

        try:
            assert not df.empty
            df.index = timeindex
        except AssertionError:
            logger.warning("No data for %s in column %s." % (name, column))

        return df

    # create config for results
    path = os.getcwd()
    # add meta_args with args of results
    config = load_config_file(path+'/tools/config.json')['results']

    # map and Database settings of etrago_from_oedb()
    _prefix = 'EgoGridPfHvResult'
    schema = 'model_draft'
    packagename = 'egoio.db_tables'
    _pkg = import_module(packagename + '.' + schema)
    temp_ormclass = 'TempResolution'
    carr_ormclass = 'Source'
    _mapped = {}

    # get metadata

    orm_meta = getattr(_pkg, _prefix + 'Meta')

    # check result_id

    result_id_in = session.query(
        orm_meta.result_id).filter(orm_meta.
                                   result_id == result_id).all()
    if result_id_in:
        logger.info('Choosen result_id %s found in DB', result_id)
    else:
        logger.info('Error: result_id not found in DB')

    # get meta data as args
    meta_args = recover_resultsettings(session, json_file, orm_meta, result_id)

    # get TempResolution
    temp = TempResolution

    tr = session.query(temp.temp_id, temp.timesteps,
                       temp.resolution, temp.start_time).one()

    timeindex = pd.DatetimeIndex(start=tr.start_time,
                                 periods=tr.timesteps,
                                 freq=tr.resolution)

    timeindex = timeindex[meta_args['eTraGo']['start_snapshot'] -
                          1: meta_args['eTraGo']['end_snapshot']]

    # create df for PyPSA network

    network = pypsa.Network()
    network.set_snapshots(timeindex)

    timevarying_override = False

    if pypsa.__version__ == '0.11.0':
        old_to_new_name = {'Generator':
                           {'p_min_pu_fixed': 'p_min_pu',
                            'p_max_pu_fixed': 'p_max_pu',
                            'source': 'carrier',
                            'dispatch': 'former_dispatch'},
                           'Bus':
                           {'current_type': 'carrier'},
                           'Transformer':
                           {'trafo_id': 'transformer_id'},
                           'Storage':
                           {'p_min_pu_fixed': 'p_min_pu',
                            'p_max_pu_fixed': 'p_max_pu',
                            'soc_cyclic': 'cyclic_state_of_charge',
                            'soc_initial': 'state_of_charge_initial',
                            'source': 'carrier'}}

        timevarying_override = True

    else:
        old_to_new_name = {'Storage':
                           {'soc_cyclic': 'cyclic_state_of_charge',
                            'soc_initial': 'state_of_charge_initial'}}

    # get data into dataframes
    logger.info('Start building eTraGo results network')
    for comp, comp_t_dict in config.items():

        orm_dict = map_ormclass(comp)

        pypsa_comp_name = 'StorageUnit' if comp == 'Storage' else comp
        ormclass = orm_dict[comp]

        if not comp_t_dict:
            df = dataframe_results(comp, session, result_id, ormclass)

            if comp in old_to_new_name:
                tmp = old_to_new_name[comp]
                df.rename(columns=tmp, inplace=True)

            network.import_components_from_dataframe(df, pypsa_comp_name)

        if comp_t_dict:

            for name, columns in comp_t_dict.items():

                name = name[:-1]
                pypsa_comp_name = name

                if name == 'Storage':
                    pypsa_comp_name = 'StorageUnit'
                if name == 'Transformer':
                    name = 'Trafo'

                for col in columns:

                    df_series = series_results(
                        name, col, session, result_id, ormclass)

                    # TODO: VMagPuSet?
                    if timevarying_override and comp == 'Generator':
                        idx = df[df.former_dispatch == 'flexible'].index
                        idx = [i for i in idx if i in df_series.columns]
                        df_series.drop(idx, axis=1, inplace=True)

                    try:

                        pypsa.io.import_series_from_dataframe(
                            network,
                            df_series,
                            pypsa_comp_name,
                            col)

                    except (ValueError, AttributeError):
                        logger.warning("Series %s of component %s could not be"
                                       " imported" % (col, pypsa_comp_name))

    logger.info('Imported eTraGo results of id = %s ', result_id)
    return network


def recover_resultsettings(session, json_file, orm_meta, result_id):
    """ Recover scenario_setting from database
    """

    # check result_id
    result_id_in = session.query(
        orm_meta.result_id).filter(orm_meta.
                                   result_id == result_id).all()

    # get meta data as json_file
    meta = session.query(orm_meta.result_id, orm_meta.scn_name,
                         orm_meta.calc_date,
                         orm_meta.user_name, orm_meta.method,
                         orm_meta.start_snapshot,
                         orm_meta.end_snapshot, orm_meta.solver,
                         orm_meta.settings
                         ).filter(orm_meta.result_id == result_id)

    meta_df = pd.read_sql(
        meta.statement, meta.session.bind, index_col='result_id')

    # update json_file with main data by result_id
    json_file['eTraGo']['scn_name'] = meta_df.scn_name[result_id]
    json_file['eTraGo']['method'] = meta_df.method[result_id]
    json_file['eTraGo']['start_snapshot'] = meta_df.start_snapshot[result_id]
    json_file['eTraGo']['end_snapshot'] = meta_df.end_snapshot[result_id]
    json_file['eTraGo']['solver'] = meta_df.solver[result_id]

    # update json_file with specific data by result_id
    meta_set = dict(meta_df.settings[result_id])

    for key in json_file['eTraGo'].keys():
        try:
            json_file['eTraGo'][key] = meta_set[key]
        except KeyError:
            pass

    return json_file


if __name__ == '__main__':
    pass
