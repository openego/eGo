Developer notes
~~~~~~~~~~~~~~~




Interface eDisGo
----------------




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





eDisGo results or output
------------------------

========= ======================================= ====
Parameter Description                             Unit
========= ======================================= ====
*Lines*



xxxx       yyy                                    MW
========= ======================================= ====
