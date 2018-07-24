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
import logging
import csv

__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke"


def define_logging(log_name='ego.log'):
    """Helpers to log your modeling process with eGo and defines all settings.

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

    # Logging
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logger = logging.getLogger(__name__)
    logger = logging.getLogger('ego')

    logger = logging.FileHandler(log_name, mode='w')

    formatter = logging.Formatter('%(asctime)s - %(name)s - \
                                   %(levelname)s - %(message)s')
    logger.setFormatter(formatter)

    # logger.addHandler(xy)

    return logger


logger = define_logging(log_name='ego.log')

# import scenario settings **args


def get_scenario_setting(jsonpath='scenario_setting.json'):
    """Get and open json file with scenaio settings of eGo.
    The settings incluede global, eTraGo and eDisGo specific
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
    print("Your path is:\n", path)

    with open(path + '/'+jsonpath) as f:
        json_file = json.load(f)

    if json_file['global'].get('eTraGo') == True:

        print('Using and importing eTraGo settings')

        # special case of SH and model_draft
        # ToDo: check and maybe remove this part
        sh_scen = ["SH Status Quo", "SH NEP 2035", "SH eGo 100"]
        if json_file['eTraGo'].get('scn_name') in sh_scen and json_file['eTraGo'].\
                get('gridversion') == "v0.4.2":
            json_file['eTraGo']['gridversion'] = None

    # add global parameter to eTraGo scn_set
    json_file['eTraGo'].update({'db': json_file['global'].get('db')})
    json_file['eTraGo'].update(
        {'gridversion': json_file['global'].get('gridversion')})

    if json_file['global'].get('eDisGo') == True:
        print('Use eDisGo settings')

    return json_file

def fix_leading_separator(csv_file, **kwargs):
    """
    Takes the path to a csv-file. If the first line this file has a leading
    separator in its header, this field is deleted. If this is done the second
    field of every row is removed, too.
    """
    with open(csv_file,'r') as f:
        lines = csv.reader(f,**kwargs)
        if not lines:
            raise Exception('File %s contained no data'%csv_file)
        first_line = next(lines)
        if first_line[0] == '':
            tmp_file = 'tmp_' + csv_file
            with open(tmp_file) as out:
                writer = csv.writer(out, **kwargs)
                writer.writerow(first_line[1:])
                for line in lines:
                    l = line[2:]
                    l.insert(0,line[0])
                    writer.writerow(l, **kwargs)
            os.rename(tmp_file, csv_file)

def fix_leading_separator(csv_file, **kwargs):
    """
    Takes the path to a csv-file. If the first line this file has a leading
    separator in its header, this field is deleted. If this is done the second
    field of every row is removed, too.
    """
    with open(csv_file, 'r') as f:
        lines = csv.reader(f, **kwargs)
        if not lines:
            raise Exception('File %s contained no data' % csv_file)
        first_line = next(lines)
        if first_line[0] == '':
            tmp_file = 'tmp_' + csv_file
            with open(tmp_file) as out:
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
