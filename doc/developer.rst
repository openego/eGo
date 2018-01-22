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


=========== ======================================= ====== ======
Parameter   Description                             Unit   exists
=========== ======================================= ====== ======
**Lines**   Results of MV calculation
index       Name of investment: line, cable                  x
length      lenght of single line                   km?      x
quantity    ??                                       ?       x
total_costs Total investment costs of cable, lines,  €/unit  x
            transformer
type        Type of used equipment                  Name     x
grid_losses Grid losses of MV Grid (time step/year?) MWh     O
**Storage**
index        Name                                   string   O
size         Size of storage                        MW       O
Capacity     capacity of storage                    MWh      O
=========== ======================================= ====== =====
