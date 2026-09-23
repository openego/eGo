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
This is the application file for the tool eGo. The application eGo calculates
the transmission and distribution grids of eTraGo and eDisGo.

.. note:: Note, the data source of eGo relies on
          the Open Energy Database. - The registration for the public
          accessible API can be found on
   `openenergy-platform.org/login <http://openenergy-platform.org/login/>`_.
"""

import os

if not "READTHEDOCS" in os.environ:
    from tools.io import eGo
    from tools.utilities import define_logging

    logger = define_logging(name="ego")

__copyright__ = (
    "Flensburg University of Applied Sciences, "
    "Europa-Universität Flensburg, "
    "Centre for Sustainable Energy Systems"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = ("wolf_bunke, maltesc, ClaraBuettner, KathiEsterl, "
              "MoritzSchloesser, joda9")


if __name__ == "__main__":

    logger.info("Start calculation")

    # Initialize eGo object
    #ego_prepare = eGo(jsonpath="scenario_settings_prepare_grids.json")

    # Run eGo
    #ego_prepare.run()
    
    #del ego_prepare
    
    # ego_select_ts_1 = eGo(jsonpath="scenario_settings_select_ts_nodg.json")
    
    # ego_select_ts_1.run()
    
    # del ego_select_ts_1
    
    # ego_select_ts_2 = eGo(jsonpath="scenario_settings_select_ts_withdg.json")
    
    # ego_select_ts_2.run()
    
    # del ego_select_ts_2
    
    # ego_select_ts_3 = eGo(jsonpath="scenario_settings_select_ts_withdg_uni.json")
    
    # ego_select_ts_3.run()
    
    # del ego_select_ts_3
    
    ego_opt_1 = eGo(jsonpath="scenario_settings_optimize_prepared_grids_nodg.json")
    
    ego_opt_1.run()
    
    # ego_opt_2 = eGo(jsonpath="scenario_settings_optimize_prepared_grids_withdg.json")
    
    # ego_opt_2.run()
    
    # ego_opt_3 = eGo(jsonpath="scenario_settings_optimize_prepared_grids_withdg_uni.json")
    
    # ego_opt_3.run()
    #ego.edisgo.network[32377]
