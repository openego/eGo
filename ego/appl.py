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
the distribution and transmission grids of eTraGo and eDisGo.

.. note:: Note, the data source of eGo relies on
          the Open Energy Database. - The registration for the public
          accessible API can be found on
   `openenergy-platform.org/login <http://openenergy-platform.org/login/>`_.
"""

import os

if not 'READTHEDOCS' in os.environ:
    from tools.io import eGo
    from tools.utilities import define_logging
    logger = define_logging(name='ego')

__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc"


if __name__ == '__main__':

    logger.info('Start calculation')

    ego = eGo(jsonpath='scenario_setting.json')
#    logger.info('Print results')
#    ego.etrago_line_loading()
#    print(ego.etrago.generator)
#    print(ego.etrago.storage_costs)
#    print(ego.etrago.operating_costs)
