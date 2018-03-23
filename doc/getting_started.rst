Getting started
###############

.. warning::

      Note, eGo, eTraGo and eDisGo relies on data provided by the OEDB. Currently, only members
      of the openego project team have access to this database. Public access
      (SQL queries wrapped by HTML) to the OEDB will be provided soon


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
``pip3 install -e eGo`` . This will install all needed packages into your environment.

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

Using eGo:
==========

1. check and prepare your eGo setting in ``ego/scenario_setting.json``
2. Start your calculation with in the directory of ``eGo/ego`` with ``python3 ego_main.py``
