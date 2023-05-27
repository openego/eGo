===
eGo
===



Overview of modules
===================


.. toctree::
   :maxdepth: 7

   ego.tools

scenario_settings.json
======================

With the ``scenario_settings.json`` file you set up your calcualtion.
The file can be found on
`github <https://github.com/openego/eGo/blob/master/ego/scenario_setting.json>`_.

.. json:object:: scenario_setting.json

   This file contains all input settings for the eGo tool.

   :property global: Global (superordinate) settings that are valid for both, eTraGo and eDisGo.
   :proptype global: :json:object:`global`
   :property eTraGo: eTraGo settings, only valid for eTraGo runs.
   :proptype eTraGo: :json:object:`eTraGo`
   :property eDisGo: eDisGo settings, only valid for eDisGo runs.
   :proptype eDisGo: :json:object:`eDisGo`


.. json:object:: global

   :property bool eTraGo: Decide if you want to run the eTraGo tool (HV/EHV grid optimization).
   :property bool eDisGo: Decide if you want to run the eDisGo tool (MV grid optimiztaion). Please note: eDisGo requires eTraGo= ``true``.
   :property string csv_import_eTraGo: ``false`` or path to previously calculated eTraGo results (in order to reload the results instead of performing a new run).
   :property string csv_import_eDisGo: ``false`` or path to previously calculated eDisGo results (in order to reload the results instead of performing a new run).


.. json:object:: eTraGo

   This section of :json:object:`scenario_setting.json` contains all input parameters for the eTraGo tool. A description of the parameters can be found `here. <https://etrago.readthedocs.io/en/dev/api/etrago.html#module-etrago.appl>`_


.. json:object:: eDisGo

   This section of :json:object:`scenario_setting.json` contains all input parameters for the eDisGo tool and the clustering of MV grids.

   :property string gridversion: This parameter is currently not used.
   :property string grid_path: Path to the MV grid files (created by `ding0 <https://readthedocs.org/projects/dingo/>`_) (e.g. ``''data/MV_grids/20180713110719''``)
   :property string choice_mode: Mode that eGo uses to chose MV grids out of the files in **grid_path** (e.g. ``''manual''``, ``''cluster''`` or ``''all''``). If ``''manual''`` is chosen, the parameter **manual_grids** must contain a list of the desired grids. If ``''cluster''`` is chosen, **no_grids** must specify the desired number of clusters and **cluster_attributes** must specify the applied cluster attributes. If ``''all''`` is chosen, all MV grids from **grid_path** are calculated.
   :property list cluster_attributes: List of strings containing the desired cluster attributes. Available attributes are all attributes returned from :py:func:`~ego.mv_clustering.mv_clustering.get_cluster_attributes.
   :property bool only_cluster: If ``true``, eGo only identifies cluster results, but performs no eDisGo run. Please note that for **only_cluster** an eTraGo run or dataset must be provided.
   :property list manual_grids: List of MV grid ID's in case of **choice_mode** = ``''manual''`` (e.g. ``[1718,1719]``). Ohterwise this parameter is ignored.
   :property int n_clusters: Number of MV grid clusters (from all grids in **grid_path**, a specified number of representative clusters is calculated) in case of **choice_mode** = ``''cluster''``. Otherwise this parameter is ignored.
   :property bool parallelization: If ``false``, eDisgo is used in a consecutive way (this may take very long time). In order to increase the performance of MV grid simulations, ``true`` allows the parallel calculation of MV grids. If **parallelization** = ``true``, **max_calc_time** and **max_workers** must be specified.
   :property float max_calc_time: Maximum calculation time in hours for eDisGo simulations. The calculation is terminated after this time and all costs are extrapolated based on the unfinished simulation. Please note that this parameter is only used if **parallelization** = ``true``.
   :property ing max_workers: Number of workers (cpus) that are allocated to the simulation. If the given value exceeds the number of available workers, it is reduced to the number of available workers. Please note that this parameter is only used if **parallelization** = ``true``.
   :property float max_cos_phi_renewable: Maximum power factor for wind and solar generators in MV grids (e.g. ``0.9``). If the reactive power (as calculated by eTraGo) exceeds this power factor, the reactive power is reduced in order to reach the power factor conditions.
   :property string solver: Solver eDisGo uses to optimize the curtailment and storage integration (e.g. ``''gurobi''``).
   :property string results: Path to folder where eDisGo's results will be saved.
   :property list tasks: List of string defining the tasks to run. The eDisGo calculation for each MV grid can be devided into separate tasks which is helpful in case one tasks fails and calculations do not need to started in the beginning. The following tasks exist: ``''1_setup_grid''``, ``''2_specs_overlying_grid''``, ``''3_temporal_complexity_reduction''``, ``''4_optimisation''``, ``''5_grid_reinforcement''``.



appl.py
===========

This is the application file for the tool eGo. The application eGo calculates
the distribution and transmission grids of eTraGo and eDisGo.

.. note:: Note, the data source of eGo relies on
          the Open Energy Database. - The registration for the public
          accessible API can be found on
          `openenergy-platform.org/login <http://openenergy-platform.org/login/>`_.

Run the ``appl.py`` file with:

.. code-block:: bash

   >>> python3 -i appl.py
   >>> ...
   >>> INFO:ego:Start calculation
   >>> ...

The eGo application works like:

.. code-block:: python

  >>> from ego.tools.io import eGo
  >>> ego = eGo(jsonpath='scenario_setting.json')
  >>> ego.etrago_line_loading()
  >>> print(ego.etrago.storage_costs)
  >>> ...
  >>> INFO:ego:Start calculation
  >>> ...
