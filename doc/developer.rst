===============
Developer notes
===============


1. Installation and getting eGo
-------------------------------

Please follow the :doc:`installation instructions <installation>` for the
recommended developer setup.


2. Get your Database login data
-------------------------------

`Learn more here <https://openego.readthedocs.io/en/dev/installation.html#setup-database-connection>`_.

3. Create Dingo grids
----------------------

Install ding0 from github.com and run the ``example_parallel_multiple_grid_districts.py``
script, which can be found under ``ding0/ding0/examples/``.

.. code-block:: bash

   $ git clone https://github.com/openego/ding0.git
   $ pip3 install -e ding0
   $ python3 ding0/ding0/examples/example_parallel_multiple_grid_districts.py

`Learn more about Dingo <https://dingo.readthedocs.io/en/dev/usage_details.html>`_.
Before you run the script check also the configs of Dingo and eDisGo in order to
use the right database version. You find this files under
``ding0/ding0/config/config_db_tables.cfg`` and
``~.edisgo/config/config_db_tables.cfg``. Your created ding0 grids are stored in
``~.ding0/..``.



eDisGo and eTraGo
-----------------

For developer installation instructions, please refer to the
`eDisGo documentation
<https://edisgo.readthedocs.io/en/dev/installation.html#developer-installation>`_
and the
`eTraGo documentation
<https://etrago.readthedocs.io/en/latest/installation.html#installation-for-developers>`_.


Error handling
--------------

1. Matplotlib errors may occur on servers and some other systems. Change the
   setting in ``matplotlibrc`` from ``backend : TkAgg`` to ``backend : PDF``.
   The file can be found, for example, in a virtual environment under
   ``~/env/lib/python3.10/site-packages/matplotlib/mpl-data/matplotlibrc``.

   `Learn more here
   <https://matplotlib.org/users/customizing.html#a-sample-matplotlibrc-file>`_.

2. A GeoPandas error may be caused by a missing Rtree
   ``libspatialindex_c`` library. Install ``libspatialindex_c`` using:

   .. code-block:: bash

      $ sudo apt install python3-rtree

   On Windows or macOS, it may be necessary to install
   ``libspatialindex_c`` from source.