===============
Getting started
===============

In order to start and run the eGo-tool a few steps needs to be done.

Steps to run eGo
================

1. Are you registered on the OpenEnergy Platform?
   The registration for the public accessible API can be found on
   `openenergy-platform.org/login `<http://openenergy-platform.org/login/>`_.

2. You have Python 3 installed? Install for example the Python
   distribution of `<https://www.anaconda.com/download>`_.

3. Install and use a virtual environment for your installation (optional).

4. Install the eGo tool ``pip3 install eGo --process-dependency-links``.

5. Create mid and low voltage distribution grids with ding0.
   Learn more about Ding0 on `<https://dingo.readthedocs.io/en/dev/index.html>`_.

6. Check and prepare your eGo setting in ``ego/scenario_setting.json``. Add your
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
on `jupyter.org <http://jupyter.org/>`_.


    `Workshop open_eGo Session eGo (in German) <https://nbviewer.jupyter.org/gist/wolfbunke/7659fbc22b9d72f0cda8dc544d1f537e>`_

    `Workshop open_eGo Session eTraGo (in German) <https://nbviewer.jupyter.org/gist/ulfmueller/2c1fd6c4c29d606b313ab32bc0391dd2/eTraGo_Session_Workshop2018.ipynb>`_
    
    `Workshop open_eGo Session DinGo (in German)<https://nbviewer.jupyter.org/gist/nesnoj/6ee605cd3494fa6e3e848385c4afbe19/dingo_session.ipynb>`_

    `Workshop open_eGo Session eDisGo (in German)<https://nbviewer.jupyter.org/gist/birgits/46aafa9d9bc860a47b18b0a1100d7dd7/edisgo_session.ipynb>`_
    
    `OpenMod eTraGo Tutorial (in English) <https://github.com/openego/eGo/blob/master/ego/examples/tutorials/etrago_OpenMod_Zuerich18.ipynb>`_
    



Example Cluster of Germany
==========================



.. raw:: html
   :file: images/iplot_cluster.html

