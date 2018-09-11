======================
Theoretical background
======================

.. contents::


Models overview
================


.. figure:: images/open_ego_models_overview.png
   :width: 1123px
   :height: 794px
   :scale: 70%
   :alt: Overview of Models and processes which are used by eGo
   :align: center


eTraGo's Theoretical Background
===================

Learn more aboute eTraGo's theoretical background of methods and assumptions
`here <https://etrago.readthedocs.io/en/latest/theoretical_background.html>`_.

eDisGo's Theoretical Background
======================

Learn more aboute eTraGo's theoretical background of methods and assumptions
`here <https://edisgo.readthedocs.io/en/latest/start_page.html>`_.


eDisGo Cluster Method
======================

In order to achieve acceptable computation times, the problem's complexity can be reduced by applying a k-means cluster-algorithm to MV grids. The algorithm identifies a specified number of representative MV grids and assigns a weighting to each grid. As described `here <https://openego.readthedocs.io/en/dev/api/modules.html#edisgo>`_, the available clustering attributes are:

* The cumulative installed **wind capacity**,
* the cumulative installed **solar capacity**,
* the distance between transition point and **farthest node** of the MV grid and
* the installed **battery capacity** (as a results of eTraGo's investment optimization).

Subsequent to the MV grid simulations with the reduced number of representative grids, the cluster weighting is used to extrapolate the costs back to the original number of MV grids.


Economic calculation
====================



References
==========
