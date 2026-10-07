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
   :property string preset: eDisGo runner preset run for every MV grid (e.g. ``''overlying_grid_opf_spatial''``). The **timestep_selection** and **spatial_reduction** settings of the example JSON files fit the presets ``''overlying_grid_opf_spatial''`` and ``''spatial_reduction_opf''``; other presets have no selection or ``spatial_reduce`` step, so eDisGo rejects these settings for them (set them to ``null``).
   :property string|object database: Database eDisGo reads from: ``''oep''``, ``''egon-data''``, ``''''`` to auto-detect, or an object with ``source`` and ``config_path``. ``null`` keeps the preset's setting. The top-level ``database`` and ``ssh`` sections only configure eGo's own database connection.
   :property object timestep_selection: Time-step selection of eDisGo, merged into the preset's block of the same name: ``task`` (``''set_timeindex''``, ``''select_critical_timesteps''`` or ``''none''``) picks the step that runs, the object named after a task holds its parameters. ``null`` keeps the preset's selection. See :ref:`edisgo-timestep-selection`.
   :property object spatial_reduction: Spatial complexity reduction of eDisGo, merged into the preset's block of the same name (e.g. ``enabled``, ``mode``, ``reduction_factor``). ``null`` keeps the preset's setting.
   :property object timestep_selection_per_grid: Settings keyed by MV grid ID as a string (e.g. ``{"32355": {"task": "none"}}``), merged into **timestep_selection** for that grid. **spatial_reduction_per_grid** works the same way for **spatial_reduction**.
   :property string results: Path to folder where eDisGo's results will be saved.
   :property list tasks: List of string defining the tasks to run. The eDisGo calculation for each MV grid can be devided into separate tasks which is helpful in case one tasks fails and calculations do not need to started in the beginning. The following tasks exist: ``''1_setup_grid''``, ``''2_specs_overlying_grid''``, ``''3_temporal_complexity_reduction''``, ``''4_optimisation''``, ``''5_grid_reinforcement''``.


.. _edisgo-timestep-selection:

eDisGo time-step selection
--------------------------

Each eDisGo preset that supports a time-step selection
(``overlying_grid_opf``, ``overlying_grid_opf_spatial``,
``spatial_reduction_opf``) contains two selection steps in its pipeline:

* ``set_timeindex`` runs early and analyses a fixed period you give.
* ``select_critical_timesteps`` runs late, after all time series are loaded,
  and picks the most critical intervals of the year itself.

``task`` in **timestep_selection** picks which of the two runs; the other one
is skipped. The parameters of a step go in the object named after it. eGo
passes the block to eDisGo, which merges it into the preset's block: keys you
leave out keep the preset's value.

**Use the preset's selection**

.. code-block:: json

   {
       "timestep_selection": null
   }

**Most critical intervals**

.. code-block:: json

   {
       "timestep_selection": {
           "task": "select_critical_timesteps",
           "select_critical_timesteps": {"method": "power_flow"}
       }
   }

``method`` is ``"power_flow"`` (critical intervals from a power flow) or
``"residual_load"`` (from the residual load; needs the eTraGo results). Further
parameters, e.g. ``time_steps_per_time_interval`` (interval length in hours,
default 168), are listed in the docstring of eDisGo's
``edisgo.run.tasks.timeseries.task_select_critical_timesteps``.

**Fixed period**

.. code-block:: json

   {
       "timestep_selection": {
           "task": "set_timeindex",
           "set_timeindex": {"start": "2035-01-15 00:00", "periods": 168}
       }
   }

Give exactly one of: ``start`` plus ``periods`` (number of hours), ``start``
plus ``end``, or a list ``timestamps``. ``spatial_reduction_opf`` already sets
``start`` and ``periods``; to use ``end`` or ``timestamps`` with it, set the
unused keys to ``null`` (e.g. ``{"end": "2035-01-21 23:00", "periods": null}``),
otherwise eDisGo reports a conflict.

**Full time series, no selection**

.. code-block:: json

   {
       "timestep_selection": {"task": "none"}
   }

**Different settings per grid**

**timestep_selection** applies to every grid. Entries in
**timestep_selection_per_grid**, keyed by MV grid ID as a string, are merged
into it for that grid, so they only need the keys that differ:

.. code-block:: json

   {
       "timestep_selection": {
           "task": "select_critical_timesteps",
           "select_critical_timesteps": {"method": "power_flow"}
       },
       "timestep_selection_per_grid": {
           "32355": {"task": "set_timeindex",
                     "set_timeindex": {"start": "2035-07-01 00:00", "periods": 24}},
           "32377": {"select_critical_timesteps": {"method": "residual_load"}}
       }
   }

Here grid 32355 analyses one fixed day, grid 32377 uses the residual load and
all other grids use the default.

The presets ``worst_case`` and ``flex_opf`` have no selection step; with them,
**timestep_selection** must be ``null``. eDisGo checks all of this before the
run and names the setting to fix.



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
