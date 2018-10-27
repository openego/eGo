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
"""This module contains utility functions for the eGo application.
"""
import csv
import os
import pandas as pd
import json
import csv
import sys
import logging
logger = logging.getLogger(__name__)

from time import localtime, strftime
if not 'READTHEDOCS' in os.environ:

    from egoio.db_tables import model_draft, grid
    from egoio.tools import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke"


def define_logging(name):
    """Helps to log your modeling process with eGo and defines all settings.

    Parameters
    ----------
    log_name : str
        Name of log file. Default: ``ego.log``.

    Returns
    -------
    logger : :class:`logging.basicConfig`.
        Set up ``logger`` object of package ``logging``
    """

    # ToDo: Logger should be set up more specific
    #       add pypsa and other logger INFO to ego.log
    now = strftime("%Y-%m-%d_%H%M%S", localtime())

    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Logging
    logging.basicConfig(stream=sys.stdout,
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logger = logging.getLogger(name)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

#    logger = logging.FileHandler(log_name, mode='w')
    fh = logging.FileHandler(
        log_dir + '/' + name + '_' + now + '.log', mode='w')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def get_scenario_setting(jsonpath='scenario_setting.json'):
    """Get and open json file with scenaio settings of eGo.
    The settings incluede eGo, eTraGo and eDisGo specific
    settings of arguments and parameters for a reproducible
    calculation.

    Parameters
    ----------
    json_file : str
        Default: ``scenario_setting.json``
        Name of scenario setting json file

    Returns
    -------
    json_file : dict
        Dictionary of json file
    """
    path = os.getcwd()
    # add try ego/
    logger.info("Your path is: {}".format(path))

    with open(path + '/' + jsonpath) as f:
        json_file = json.load(f)

    # fix remove result_id
    json_file['eGo'].update({'result_id': None})

    # check settings
    if (json_file['eGo']['eTraGo'] is False and json_file['eGo']['eDisGo']
            is False):
        logger.warning("Something went wrong! \n"
                       "Please contoll your settings and restart. \n"
                       "Set at least eTraGo = true")
        return

    if (json_file['eGo']['eTraGo'] is None and json_file['eGo']['eDisGo']
            is None):
        logger.warning("Something went wrong! \n"
                       "Please contoll your settings and restart. \n"
                       "Set at least eTraGo = true")
        return

    if json_file['eGo']['result_id'] and json_file['eGo']['csv_import_eTraGo']:
        logger.warning(
            "You set a DB result_id and a csv import path! \n"
            "Please remove on of this settings")
        return
        # or ? json_file['eGo']['result_id'] = None

    if json_file['eGo']['eTraGo'] is None and json_file['eGo']['eDisGo']:
        logger.info(
            "eDisGo needs eTraGo results. Please change your settings!\n")
        return

    if json_file['eGo']['eTraGo'] is False and json_file['eGo']['eDisGo']:
        logger.info(
            "eDisGo needs eTraGo results. Please change your settings!\n")
        return

    if (json_file['eGo']['result_id'] is None and
            json_file['eGo']['csv_import_eTraGo'] is None):
        logger.info(
            "No data import from results is set \n"
            "eGo runs by given settings")

    if (json_file['eGo']['csv_import_eTraGo'] and
            json_file['eGo']['csv_import_eDisGo']):
        logger.info(
            "eDisGo and eTraGo results will be imported from csv\n")

    if json_file['eGo'].get('eTraGo') == True:

        logger.info('Using and importing eTraGo settings')

        # special case of SH and model_draft
        # TODO: check and maybe remove this part
        sh_scen = ["SH Status Quo", "SH NEP 2035", "SH eGo 100"]
        if json_file['eTraGo'].get('scn_name') in sh_scen and json_file['eTraGo'].\
                get('gridversion') is not None:
            json_file['eTraGo']['gridversion'] = None

        if json_file['eTraGo'].get('extendable') == "['network', 'storages']":
            json_file['eTraGo'].update({'extendable': ['network', 'storage']})

        if json_file['eTraGo'].get('extendable') == "['network', 'storage']":
            json_file['eTraGo'].update({'extendable': ['network', 'storage']})

        if json_file['eTraGo'].get('extendable') == "['network']":
            json_file['eTraGo'].update({'extendable': ['network']})

        if json_file['eTraGo'].get('extendable') == "['storages']":
            json_file['eTraGo'].update({'extendable': ['storage']})

        if json_file['eTraGo'].get('extendable') == "['storage']":
            json_file['eTraGo'].update({'extendable': ['storage']})

    if json_file['eGo'].get('eDisGo') == True:
        logger.info('Using and importing eDisGo settings')

    return json_file


def fix_leading_separator(csv_file, **kwargs):
    """
    Takes the path to a csv-file. If the first line of this file has a leading
    separator in its header, this field is deleted. If this is done the second
    field of every row is removed, too.
    """
    with open(csv_file, 'r') as f:
        lines = csv.reader(f, **kwargs)
        if not lines:
            raise Exception('File %s contained no data' % csv_file)
        first_line = next(lines)
        if first_line[0] == '':
            path, fname = os.path.split(csv_file)
            tmp_file = os.path.join(path, 'tmp_' + fname)
            with open(tmp_file, 'w+') as out:
                writer = csv.writer(out, **kwargs)
                writer.writerow(first_line[1:])
                for line in lines:
                    l = line[2:]
                    l.insert(0, line[0])
                    writer.writerow(l, **kwargs)
            os.rename(tmp_file, csv_file)


def get_time_steps(json_file):
    """ Get time step of calculation by scenario settings.

    Parameters
    ----------
    json_file : :obj:`dict`
        Dictionary of the ``scenario_setting.json`` file

    Returns
    -------
    time_step : int
        Number of timesteps of the calculation.
    """

    end = json_file['eTraGo'].get('end_snapshot')
    start = json_file['eTraGo'].get('start_snapshot')
    time_step = end - start

    return time_step


def open_oedb_session(ego):
    """
    """
    _db_section = ego.json_file["eTraGo"]["db"]
    conn = db.connection(section=_db_section)
    session_factory = sessionmaker(bind=conn)
    Session = scoped_session(session_factory)
    session = Session()

    return session
