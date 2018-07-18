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

   This file contains all input settings for the eGo tool.

   :property global: Global settings that are valid for both eTraGo and eDisGo
   :proptype global: :json:object:`global`
   :property eTraGo: eTraGo settings, only valid for eTraGo run
   :proptype eTraGo: :json:object:`eTraGo`
   :property eDisGo: eDisGo settings, only valid for eDisGo runs
   :proptype eDisGo: :json:object:`eDisGo`


.. json:object:: global
   
   :property bool eTraGo: Decide if you want to run the eTraGo tool (HV/EHV grid optimization).
   :property bool eDisGo: Decide if you want to run the eDisGo tool (MV grid optimiztaion).
   :property string db: Name of your database (e.g.``''oedb''``).
   :property bool recover: If ``true``, (previously calculated) eTraGo results are queried from your database (instead of performing a new run).
   :property int result_id: ID of the (previeously calculated) eTraGo results that are queried if **recover** is set ``true``.
   :property string gridversion: Version of the *open_eGo* input data-sets (e.g. ``''v0.4.2''``) 

   
.. json:object:: eTraGo

   This section of :json:object:`scenario_setting.json` contains all input parameters for the eTraGo tool. A description of the parameters can be found `here. <https://etrago.readthedocs.io/en/dev/api/etrago.html#module-etrago.appl>`_

   Please note that some parameters are already included in :json:object:`global`
	

.. json:object:: eDisGo

   This section of :json:object:`scenario_setting.json` contains all input parameters for the eDisGo tool and the Clustering of MV grids.

   :property string ding0_files: Relative path to the MV grid files (created by `ding0 <https://readthedocs.org/projects/dingo/>`_) (e.g. ``''data/MV_grids/20180713110719''``)
   :property string choice_mode: Mode that eGo uses to chose MV grids out of the files in **ding0_files** (e.g. ``''manual''``, ``''cluster''`` or ``''all''``). If ``''manual''`` is chosen, the parameter **manual_grids** must contain a list of the desired grids. If ``''cluster''`` is chosen, **no_grids** must specify the desired number of clusters. If ``''all''`` is chosen, all MV grids from **ding0_files** are calculated.
   :property list manual_grids: List of MV grid ID's (*open_eGo* HV/MV substation ID's)
   :property int no_grids: Number of MV grid clusters (from all files in **ding0_files**, a specified number of representative clusters is calculated)
   
   

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
