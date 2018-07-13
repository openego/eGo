===============
Getting started
===============


How to use eGo?
===============

1. Check and prepare your eGo setting in ``ego/scenario_setting.json``
2. Start your calculation with predefined results tools and run under
   ``eGo/ego`` the main file with ``>>> python3 ego_main.py``


.. code-block:: bash

   >>> python3 ego_main.py
   >>> ...
   >>> INFO:ego:Start calculation
   >>> ...


Examples
========

.. code-block:: python

    # import the eGo tool
    from ego.tools.io import eGo

    # Run your scenario
    ego = eGo(jsonpath='scenario_setting.json')

    # Analyse your results on extra high voltage level (etrago)
    ego.etrago_line_loading()


Reesult Examples k=30 Cluster Plot of Germany
=============================================


.. raw:: html
   :file: images/iplot_k30_cluster.html
