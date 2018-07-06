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
import os
import pandas as pd
import json
import logging

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
        Name of log file. Default: ``ego.log``

    Results
    -------
    ego_logger : :class:`logging.basicConfig`.
        Set up ``ego_logger`` object of package ``logging``
    """
    # ToDo: Logger should be set up more specific
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Logging
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logger = logging.getLogger(__name__)
    ego_logger = logging.getLogger('ego')

    fh = logging.FileHandler(log_name, mode='w')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - \
                                   %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    ego_logger.addHandler(fh)

    return ego_logger


logger = define_logging(log_name='ego.log')

# import scenario settings **args


def get_scenario_setting(json_file='scenario_setting.json'):
    """Get and open json file with scenaio settings of eGo.
    The settings incluede global, eTraGo and eDisGo specific
    settings of arguments and parameters for a reproducible
    calculation.

    Parameters
    ----------
    json_file : str
        Default: ``scenario_setting.json``
        Name of scenario setting json file

    Results
    -------
    scn_set : dict
        Dictionary of json file
    """
    path = os.getcwd()
    # add try ego/
    print("Your path is:\n", path)

    with open(path + '/'+json_file) as f:
        scn_set = json.load(f)

    if scn_set['global'].get('eTraGo') == True:

        print('Using and importing eTraGo settings')

        # special case of SH and model_draft
        # ToDo: check and maybe remove this part
        sh_scen = ["SH Status Quo", "SH NEP 2035", "SH eGo 100"]
        if scn_set['eTraGo'].get('scn_name') in sh_scen and scn_set['eTraGo'].\
                get('gridversion') == "v0.4.2":
            scn_set['eTraGo']['gridversion'] = None

    # add global parameter to eTraGo scn_set
    scn_set['eTraGo'].update({'db': scn_set['global'].get('db')})
    scn_set['eTraGo'].update(
        {'gridversion': scn_set['global'].get('gridversion')})

    if scn_set['global'].get('eDisGo') == True:
        print('Use eDisGo settings')

    return scn_set


def get_time_steps(scn_set):
    """ Get time step of calculation by scenario settings.

    Parameters
    ----------
    scn_set : dict
        dict of ``scenario_setting.json``

    Returns
    -------
    time_step : int
        Number of timesteps of the calculation.
    """

    end = args['eTraGo'].get('end_snapshot')
    start = args['eTraGo'].get('start_snapshot')
    time_step = end - start

    return time_step
