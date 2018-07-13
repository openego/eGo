===============
Developer notes
===============


Installation
============

.. note::
      Installation is only tested on (Ubuntu like) linux OS.

1. Create a virtualenvironment (where you like it) and activate it:

    ``$virtualenv --clear -p python3.5  ego_dev`` and ``$ cd ego_dev/``
    followed by ``$ source bin/activate``


2. Clone eGo from github.com by running following command in your terminal:

    ```
    git clone https://github.com/openego/eGo
    ```

With your activated environment `cd` to the cloned directory and run
``pip3 install -e eGo --process-dependency-links --allow-all-external`` . This will install all needed packages into your environment.

.. warning::

      Note, that the first release for deveolper is partly dependent on
      forks and developent versions which could not automaticly be installed.
      Check your installed packages using ``pip3 freeze`` with the
      `ego_dependencies.txt <https://github.com/openego/eGo/blob/dev/ego_dependencies.txt>`_


3. Temporary solution:

After your installation install the eGo PyPSA fork on `dev <https://github.com/openego/PyPSA/tree/dev>`_
``pip3 install -e git+https://github.com/openego/PyPSA.git@dev#egg=PyPSA``
and Folium for an web based ploting with
``pip3 install -e git+git@github.com:python-visualization/folium.git@5739244acb9868d001032df288500a047b232857#egg=folium``

Check if the `config.json <https://github.com/openego/eTraGo/blob/dev/etrago/tools/config.json>`_
file from eTraGo is installed in your libary ``/lib/python3.5/site-packages/etrago/tools`` .
If not copy and paste this file into this folder.

If Database connection or table erros appears use: ``pip3 install -e git+git@github.com:openego/ego.io.git@3b76dfddea14d67eb4421b6223bf981d8851e4e6#egg=ego.io``








Interface eDisGo for grid and storage costs
===========================================


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
==================================

`grid expansion costs <http://edisgo.readthedocs.io/en/dev/api/edisgo.grid.html#edisgo.grid.network.Results.grid_expansion_costs>`_

Definition of storage exansion
------------------------------

`Attributes according to PyPSA <https://pypsa.org/doc/components.html#storage-unit>`_

Change of units from Mega to kilo:

.. csv-table:: List of variables and units
   :file: storage_units.csv
   :delim: ,
   :header-rows: 1
