===
ego
===



Overview of modules
===================


.. toctree::
   :maxdepth: 7

   ego.tools
   
   

ego_main.py
===========

This is the application file for the tool eGo. The application eGo calculates
the distribution and transmission grids of eTraGo and eDisGo.

.. note:: Note, the data source of eGo relies on
          the Open Energy Database. - The registration for the public
          accessible API can be found on
          `openenergy-platform.org/login <http://openenergy-platform.org/login/>`_.

Run the ``ego_main.py`` file with:

.. code-block:: bash

   >>> python3 ego_main.py
   >>> ...
   >>> INFO:ego:Start calculation
   >>> ...

The eGo App works like:

.. code-block:: python

  >>> from ego.tools.io import eGo
  >>> ego = eGo(jsonpath='scenario_setting.json')
  >>> ego.etrago_line_loading()
  >>> print(ego.etrago.storage_costs)
  >>> ...
  >>> INFO:ego:Start calculation
  >>> ...
