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
    # import geopandas as gpd

    from shapely.geometry import Polygon, Point, MultiPolygon
    from sqlalchemy import MetaData, create_engine,  and_, func
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.automap import automap_base
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
        edisgo_grid_investment,
        get_generator_investment)
    from ego.tools.utilities import (get_scenario_setting,
                                     get_time_steps, fix_leading_separator)
    from ego.tools.edisgo_integration import EDisGoNetworks
    from egoio.db_tables.model_draft import RenpassGisParameterRegion
    from egoio.db_tables import model_draft, grid
    from etrago.tools.plot import (plot_line_loading, plot_stacked_gen,
                                   curtailment, gen_dist, storage_distribution,
                                   plot_voltage, plot_residual_load,
                                   plot_line_loading_diff, full_load_hours,
                                   extension_overlay_network)
    from etrago.appl import etrago
    from importlib import import_module
    import pypsa
    import re

__copyright__ = ("Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc"


class egoBasic(object):
    """The eGo basic class select and creates based on your
    ``scenario_setting.json`` file  your definde eTraGo and
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

    def __init__(self,
                 jsonpath, *args, **kwargs):

        self.jsonpath = 'scenario_setting.json'
        self.json_file = get_scenario_setting(self.jsonpath)

        # Database connection from json_file
        try:
            conn = db.connection(section=self.json_file['global']['db'])
            Session = sessionmaker(bind=conn)
            self.session = Session()
            logger.info('Connected to Database')
        except:
            logger.error('Failed connection to Database',  exc_info=True)

        # get scn_name
        self.scn_name = self.json_file['eTraGo']['scn_name']

        pass

    pass


class eTraGoResults(egoBasic):
    """The ``eTraGoResults`` class create and contains all results
    of eTraGo  and it's network container for eGo.

    Returns
    -------
    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    etrago: :pandas:`pandas.Dataframe<dataframe>`
        DataFrame which collects several eTraGo results
    """

    def __init__(self, jsonpath, *args, **kwargs):
        """
        """
        super(eTraGoResults, self).__init__(self, jsonpath,
                                            *args, **kwargs)

        self.etrago_network = None
        self.etrago_disaggregated_network = None

        logger.info('eTraGoResults startet')

        if self.json_file['global']['recover'] is True:

            # Delete arguments from scenario_setting
            logger.info('Remove given eTraGo settings from scenario_setting')

            try:
                self.json_file['global']['eTraGo'] = False

                for i in self.json_file['eTraGo'].keys():

                    self.json_file['eTraGo'][i] = 'removed by recover'

                # ToDo add scenario_setting for results
                self.json_file['eTraGo']['db'] = self.json_file['global']['db']
                logger.info(
                    'Add eTraGo scenario_setting from oedb result')
                # To do ....
                _prefix = 'EgoGridPfHvResult'
                schema = 'model_draft'
                packagename = 'egoio.db_tables'
                _pkg = import_module(packagename + '.' + schema)

                # get metadata
                # version = json_file['global']['gridversion']

                orm_meta = getattr(_pkg, _prefix + 'Meta')
                self.jsonpath = recover_resultsettings(self.session,
                                                       self.json_file,
                                                       orm_meta,
                                                       self.json_file['global']
                                                       ['result_id'])

            except KeyError:
                pass

            logger.info('Create eTraGo network from oedb result')
            self.etrago_network = etrago_from_oedb(self.session, self.json_file)

        # create eTraGo NetworkScenario
        if self.json_file['global']['eTraGo'] is True:

            if self.json_file['global'].get('csv_import') != False:

                logger.info('Caution, import disaggregation '
                            'data of former Cluster')

                # get folder
                path = os.getcwd()
                folder = '/' + self.json_file['global'].get('csv_import')

                # TODO clean network.csv from folder

                try:
                    # create Network from csv
                    self.etrago_network = pypsa.Network()
                    self.etrago_network.import_from_csv_folder(path+folder)
                    logger.info('Create eTraGo network from CSV result')

                    # get disaggregation
                    self.etrago_disaggregated_network = pypsa.Network()
                    self.etrago_disaggregated_network.\
                        import_from_csv_folder(path+folder+'/disaggregated')
                    logger.info('Create eTraGo disaggregated network '
                                'from CSV result')

                except TypeError:
                    file_path = "disaggregated/network.csv"
                    fix_leading_separator(path+folder+"/"+file_path)

                    file_path = "network.csv"
                    fix_leading_separator(path+folder+"/"+file_path)

                    self.etrago_network = pypsa.Network()
                    self.etrago_network.import_from_csv_folder(path+folder)
                    logger.info('Create eTraGo network from CSV result')

                    # get disaggregation
                    self.etrago_disaggregated_network = pypsa.Network()
                    self.etrago_disaggregated_network.\
                        import_from_csv_folder(path+folder+'/disaggregated')
                    logger.info('Create eTraGo disaggregated network'
                                'from CSV result')

                args_name = "args.json"
                with open(path + folder+'/'+args_name) as f:
                    etrago_args = json.load(f)
                    logger.info('Using argument file')

                    for key in self.json_file['eTraGo'].keys():
                        try:
                            self.json_file['eTraGo'][key] = etrago_args[key]
                        except KeyError:
                            pass

            else:
                logger.info('Create eTraGo network by eGo')

                etrago_network, etrago_disaggregated_network = etrago(
                    self.json_file['eTraGo'])

                self.etrago_network = etrago_network
                self.etrago_disaggregated_network = etrago_disaggregated_network

        # add selected results to Results container

        self.etrago = pd.DataFrame()
        # self.etrago.storage_investment_costs = etrago_storages_investment(
        #    self.etrago_network, self.json_file)
        #self.etrago.storage_charges = etrago_storages(self.etrago_network)
        # self.etrago.operating_costs = etrago_operating_costs(
        #    self.etrago_network)
        self.etrago.generator = create_etrago_results(self.etrago_network,
                                                      self.scn_name)
        self.etrago.grid_investment_costs = etrago_grid_investment(self.
                                                                   etrago_network,
                                                                   self.json_file)

        # add functions direct
        # self.etrago_network.etrago_line_loading = etrago_line_loading

        pass

    if not 'READTHEDOCS' in os.environ:
        # include eTraGo functions and methods
        def etrago_line_loading(self, **kwargs):
            """
            Integrate and use function from eTraGo.
            For more information see:
            """
            # add if time_step <1  -> plot
            return plot_line_loading(network=self.etrago_network, **kwargs)

        def etrago_stacked_gen(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return plot_stacked_gen(network=self.etrago_network, **kwargs)

        def etrago_curtailment(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return curtailment(network=self.etrago_network, **kwargs)

        def etrago_gen_dist(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return gen_dist(network=self.etrago_network, **kwargs)

        def etrago_storage_distribution(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return storage_distribution(network=self.etrago_network, **kwargs)

        def etrago_voltage(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return plot_voltage(network=self.etrago_network, **kwargs)

        def etrago_residual_load(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return plot_residual_load(network=self.etrago_network, **kwargs)

        def etrago_line_loading_diff(self, networkB, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return plot_line_loading_diff(networkA=self.etrago_network,
                                          networkB=networkB, **kwargs)

        def etrago_extension_overlay_network(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return extension_overlay_network(network=self.etrago_network,
                                             **kwargs)

        def etrago_full_load_hours(self, **kwargs):
            """
            Integrate function from eTraGo.
            For more information see:
            """
            return full_load_hours(network=self.etrago_network, **kwargs)

    # add other methods from eTraGo here


class eDisGoResults(eTraGoResults):
    """The ``eDisGoResults`` class create and contains all results
    of eDisGo and its network containers.

    """

    def __init__(self, jsonpath, *args, **kwargs):
        super(eDisGoResults, self).__init__(self, jsonpath, *args, **kwargs)

        self._edisgo = None
        self._edisgo_networks = None

        if self.json_file['global']['eDisGo'] is True:
            logger.info('Create eDisGo networks')

            self._edisgo = pd.DataFrame()

            self._edisgo_networks = EDisGoNetworks(
                json_file=self.json_file,
                etrago_network=self.etrago_disaggregated_network)

            self._edisgo.grid_investment_costs = edisgo_grid_investment(
                self._edisgo_networks,
                self.json_file
            )

    @property
    def edisgo_networks(self):
        """
        Container for eDisGo grids, including all results

        Returns
        -------
        :obj:`dict` of :class:`edisgo.grid.network.EDisGo`
            Dictionary of eDisGo objects, keyed by MV grid ID

        """
        return self._edisgo_networks

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
    """Main eGo module which including all results and main functionalities.


    Returns
    -------
    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    edisgo_networks : :class:`ego.tools.edisgo_integration.EDisGoNetworks`
        Contains multiple eDisGo networks
    edisgo : :pandas:`pandas.Dataframe<dataframe>`
        aggregated results of eDisGo
    etrago : :pandas:`pandas.Dataframe<dataframe>`
        aggregated results of eTraGo


    """

    def __init__(self, jsonpath, *args, **kwargs):
        super(eGo, self).__init__(self, jsonpath,
                                  *args, **kwargs)

        # super().__init__(eDisGo)
        self.total = pd.DataFrame()
        # add total results here
        # self.total_investment_costs = pd.DataFrame()
        # self.total_operation_costs = pd.DataFrame()  # TODO

    def total_investment_cost(self):
        """ Get total investment costs of all voltage level for storages
        and grid expansion
        """

        self._total_inv_cost = pd.DataFrame(columns=['component',
                                                     'voltage_level',
                                                     'capital_cost'])
        _grid_ehv = None
        if 'network' in self.json_file['eTraGo']['extendable']:
            _grid_ehv = self.etrago.grid_investment_costs  # .capital_cost.sum()

            self._total_inv_cost = self._total_inv_cost.\
                append({'component': ' EHV HV grid',
                        'voltage_level': 'voltage_level',
                        'capital_cost': _grid_ehv.capital_cost.sum()},
                       ignore_index=True)

        _storage = None
        if 'storages' in self.json_file['eTraGo']['extendable']:
            _storage = self.etrago.grid_investment_costs  # .capital_cost.sum()

            self._total_inv_cost = self._total_inv_cost.\
                append({'component': 'storage',
                        'voltage_level': 'ehv hv grid',
                        'capital_cost': _storage.capital_cost.sum()},
                       ignore_index=True)

        _grid_mv_lv = None
        if self.json_file['global']['eDisGo'] is True:

            _grid_mv_lv = self.edisgo.grid_investment_costs  # .capital_cost.sum()

            self._total_inv_cost = self._total_inv_cost.\
                append({'component': 'mv-lv grid',
                        'voltage_level': 'mv lv grid',
                        'capital_cost': _grid_mv_lv.capital_cost.sum()},
                       ignore_index=True)

        self.total_investment_costs = self._total_inv_cost
        self.storage_costs = _storage
        self.ehv_grid_costs = _grid_ehv
        self.mv_grid_costs = _grid_mv_lv

    def plot_total_investment_costs(self):
        """ Plot total investment costs
        """
        self.total_investment_cost()

        return self.total_investment_cost.plot.bar(x='voltage_level',
                                                   y='capital_cost', rot=1)

    # write_results_to_db():
    logging.info('Initialisation of eGo Results')


# def geolocation_buses(network, session):
#     """
#     Use Geometries of buses x/y(lon/lat) and Polygons
#     of Countries from RenpassGisParameterRegion
#     in order to locate the buses
#
#     Parameters
#     ----------
#     network_etrago: : class: `etrago.tools.io.NetworkScenario`
#         eTraGo network object compiled by: meth: `etrago.appl.etrago`
#     session: : sqlalchemy: `sqlalchemy.orm.session.Session < orm/session_basics.html >`
#         SQLAlchemy session to the OEDB
    #
    # """
    # # ToDo: check eTrago stack generation plots and other in order of adaptation
    # # Start db connetion
    # # get renpassG!S scenario data
    #
    # meta = MetaData()
    # meta.bind = session.bind
    # conn = meta.bind
    # # get db table
    # meta.reflect(bind=conn, schema='model_draft',
    #              only=['renpass_gis_parameter_region'])
    #
    # # map to classes
    # Base = automap_base(metadata=meta)
    # Base.prepare()
    # RenpassGISRegion = Base.classes.renpass_gis_parameter_region
    #
    # # Define regions
    # region_id = ['DE', 'DK', 'FR', 'BE', 'LU',
    #              'NO', 'PL', 'CH', 'CZ', 'SE', 'NL']
    #
    # query = session.query(RenpassGISRegion.gid, RenpassGISRegion.u_region_id,
    #                       RenpassGISRegion.stat_level, RenpassGISRegion.geom,
    #                       RenpassGISRegion.geom_point)
    #
    # # get regions by query and filter
    # Regions = [(gid, u_region_id, stat_level, shape.to_shape(geom),
    #             shape.to_shape(geom_point)) for gid, u_region_id, stat_level,
    #            geom, geom_point in query.filter(RenpassGISRegion.u_region_id.
    #                                             in_(region_id)).all()]
    #
    # crs = {'init': 'epsg:4326'}
    # # transform lon lat to shapely Points and create GeoDataFrame
    # points = [Point(xy) for xy in zip(network.buses.x,  network.buses.y)]
    # bus = gpd.GeoDataFrame(network.buses, crs=crs, geometry=points)
    # # Transform Countries Polygons as Regions
    # region = pd.DataFrame(
    #     Regions, columns=['id', 'country', 'stat_level', 'Polygon', 'Point'])
    # re = gpd.GeoDataFrame(region, crs=crs, geometry=region['Polygon'])
    # # join regions and buses by geometry which intersects
    # busC = gpd.sjoin(bus, re, how='inner', op='intersects')
    # # busC
    # # Drop non used columns
    # busC = busC.drop(['index_right', 'Point', 'id', 'Polygon',
    #                   'stat_level', 'geometry'], axis=1)
    # # add busC to eTraGo.buses
    # network.buses['country_code'] = busC['country']
    #
    # # close session
    # session.close()
    #
    # return network


def results_to_excel(ego):
    """
    Wirte results to excel
    """
    # Write the results as xlsx file
    # ToDo add time of calculation to file name
    # add xlsxwriter to setup
    writer = pd.ExcelWriter('open_ego_results.xlsx', engine='xlsxwriter')

    # write results of installed Capacity by fuels
    ego.total.to_excel(writer, index=False, sheet_name='Total Calculation')

    # write orgininal data in second sheet
    ego.to_excel(writer, index=True, sheet_name='Results by carriers')
    # add plots

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    # buses


def etrago_from_oedb(session, json_file):
    """Function which import eTraGo results for the Database by
    ``result_id`` and if ``recover`` is set to ``true``.

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

    result_id = json_file['global']['result_id']

    # functions
    def map_ormclass(name):
        """
        Function to map sqlalchemy classes
        """
        try:
            _mapped[name] = getattr(_pkg, _prefix + name)

        except AttributeError:
            print('Warning: Relation %s does not exist.' % name)

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
            print("No data for %s in column %s." % (name, column))

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
    # version = json_file['global']['gridversion']

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
                        print("Series %s of component %s could not be "
                              "imported" % (col, pypsa_comp_name))

    print('Done')
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
    meta = session.query(orm_meta.result_id, orm_meta.scn_name, orm_meta.calc_date,
                         orm_meta.user_name, orm_meta.method, orm_meta.start_snapshot,
                         orm_meta.end_snapshot, orm_meta.solver, orm_meta.settings
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
