===
ego
===



Overview of modules
===================


.. toctree::
   :maxdepth: 7

   ego.tools
   
scenario_settings.json
======================

https://sphinx-jsondomain.readthedocs.io/en/latest/examples.html#github-user
https://etrago.readthedocs.io/en/latest/api/etrago.html#module-etrago.appl

.. json:object:: scenario_setting.json

   Text Text scenario_setting.json



   :property global: Global settings
   :proptype global: :json:object:`global setting`
   :property eTraGo: eDisGo settings
   :proptype eTraGo: :json:object:`eTraGo settings`
   :property eDisGo: eDisGo settings
   :proptype eDisGo: :json:object:`eDisGo settings`


.. json:object:: global settings
  
    Text Text
   
   
   :property bool eTraGo: ``true`` or ``false``
   :property bool eDisGo: ``true`` or ``false``...
   :property string db: Name od db, default="oedb"
   

.. json:object:: eTraGo settings
    
    Text Text
   
   
   :property bool pf_post_lopf: ``true`` or ``false``
   :property string method: "lopf
   :property int start_snapshot: Start hour of calcualtion
   

       
.. json:object:: eDisGo settings
       
    Text Text
   
   
   :property pf_post_lopf: ``true`` or ``false``
   :property method: "lopf
   :property int start_snapshot: Start hour of calcualtion
   

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
