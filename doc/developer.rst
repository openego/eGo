Developer notes
~~~~~~~~~~~~~~~



Interface eDisGo for grid and storage costs
-------------------------------------------


.. code-block:: python

    # get setting from eTraGo for eDisGo
    specs = get_etragospecs_from_db(session, bus_id, result_id, scn_name)
    ...
    # Create scenario or eDisGo of one mv Grid
    scenario = Scenario(etrago_specs=specs,
                        power_flow=(),
                        mv_grid_id=mv_grid_id,
                        scenario_name='NEP 2035')
    ...
    # import ding0 mv grid
    network = Network.import_from_ding0(file_path,
                                        id=mv_grid_id,
                                        scenario=scenario)


eDisGo units
------------

.. csv-table:: List of variables and units
   :url: https://raw.githubusercontent.com/openego/eDisGo/dev/doc/units_table.csv
   :delim: ;
   :header-rows: 1
   :widths: 5, 1, 1, 5
   :stub-columns: 0


Definition of grid expansion costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`grid expansion costs <http://edisgo.readthedocs.io/en/dev/api/edisgo.grid.html#edisgo.grid.network.Results.grid_expansion_costs>`_

Definition of storage exansion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
`Attributes according to PyPSA <https://pypsa.org/doc/components.html#storage-unit>`_

Change of units from Mega to kilo:

.. csv-table:: List of variables and units
   :file: storage_units.csv
   :delim: ,
   :header-rows: 1
