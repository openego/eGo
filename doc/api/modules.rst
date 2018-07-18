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
