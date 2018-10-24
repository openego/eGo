===============
Getting started
===============

In order to start and run the Tool eGO few steps needs to be done. 

Steps to run eGo
================

1. Are you registert on the OpenEnergy-Platform?
   The registration for the public accessible API can be found on
   `openenergy-platform.org/login `<http://openenergy-platform.org/login/>`_.

2. You have Python 3 installed? Install for example the Python 
   Distribution of `<https://www.anaconda.com/download>`_.

3. Install and use a virtual environment for you installation (optional). 

4. Install the eGo tool ``pip3 install eGo --process-dependency-links``

5. Create your distribute grids of  mid and low voltage grids with ding0. 
   Learn more about Ding0 on `<https://dingo.readthedocs.io/en/dev/index.html>`_.

6. Check and prepare your eGo setting in ``ego/scenario_setting.json``. Add you
   local paths and prepare your parameters.

7. Start your calculation and run the tool for example under
   ``eGo/ego`` and ``>>> python3 appl.py`` . You can also use any other Python
   Terminal, Jupyter Notebook or Editor.

  

How to use eGo?
===============
 
Start and use eGo from the terminal.

.. code-block:: bash

   >>> python3 appl.py
   >>> ...
   >>> INFO:ego:Start calculation
   >>> ...



Examples
--------
Inside the appl.py

.. code-block:: python

    # import the eGo tool
    from ego.tools.io import eGo

    # Run your scenario
    ego = eGo(jsonpath='scenario_setting.json')

    # Analyse your results on extra high voltage level (etrago)
    ego.etrago_line_loading()



Tutorials as Jupyter Notebook
=============================

Learn more about Jupyter Notebook and how to install and use it
on `<http://jupyter.org/>`_.


.. toctree::
   :maxdepth: 2
   
   `OpenMod eTraGo Tutorial <https://github.com/openego/eGo/blob/master/ego/examples/tutorials/etrago_OpenMod_Zuerich18.ipynb>`_



Example Cluster of Germany
==========================



.. raw:: html
   :file: images/iplot_cluster.html

