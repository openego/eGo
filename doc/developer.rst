===============
Developer notes
===============


Installation
============

.. note::
      Installation is only tested on (Ubuntu 16.04 ) linux OS.

Please read the Installation Guideline :ref:`ego.doc.installation`.   
     

1. Use virtual environment
--------------------------

Create a virtualenvironment  and activate it:

.. code-block:: bash

   $ virtualenv --clear -p python3.5  ego_dev``
   $ cd ego_dev/
   $ source bin/activate


2. Get eGo
----------

Clone eGo from github.com by running the following command in your terminal:

.. code-block:: bash

   $ git clone https://github.com/openego/eGo


With your activated environment `cd` to the cloned directory and run
``pip3 install -e eGo --process-dependency-links`` .
This will install all needed packages into your environment.

3. Get your Database login data
-------------------------------

`Learn more here <https://openego.readthedocs.io/en/dev/installation.html#setup-database-connection>`_.

4. Create Dingo grids
----------------------

Install ding0 from github.com and run the ``example_parallel_multiple_grid_districts.py``
script, which can be found under ``ding0/ding0/examples/``.

.. code-block:: bash

   $ git clone https://github.com/openego/ding0.git
   $ pip3 install -e ding0
   $ python3 ding0/ding0/examples/example_parallel_multiple_grid_districts.py

`Learn more about Dingo <https://dingo.readthedocs.io/en/dev/usage_details.html>`_.
Before you run the script check also the configs of Dingo and eDisGo in order to
use the right database version. You finde this files unter  
``ding0/ding0/config/config_db_tables.cfg`` and 
``~.edisgo/config/config_db_tables.cfg``. Your created ding0 grids are stored in
``~.ding0/..``. 
 


eDisGo and eTraGo
-----------------

Please read the Developer notes of 
`eDisGo <https://edisgo.readthedocs.io/en/dev/dev_notes.html>`_ and 
`eTraGo <https://etrago.readthedocs.io/en/latest/developer_notes.html>`_.


Error handling
--------------

1. Installation Error use pip-18.1 for you installation.
   ``pip install --upgrade pip==18.1``

2. Installation Error of eTraGo, eDisGo, Pypsa fork or ding0.
   If you have problems with one of those packages please clone it from 
   *github.com* and install it from the master or dev branch. For example
   ``pip3 install -e git+https://github.com/openego//PyPSA.git@master#egg=pypsafork``

3. Matplotlib error on server and few other systems. Please change your settings
   in ``matplotlibrc`` from ``backend : TkAgg`` to ``backend : PDF``. You can 
   find the file for example in a virtual environment under
   ``~/env/lib/python3.5/site-packages/matplotlib/mpl-data$ vim matplotlibrc``.
   `Learn more here. <https://matplotlib.org/users/customizing.html#a-sample-matplotlibrc-file>`_.

