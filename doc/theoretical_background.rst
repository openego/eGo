======================
Theoretical background
======================

.. contents::


Models overview
===============


.. figure:: images/open_ego_models_overview.png
   :width: 1123px
   :height: 794px
   :scale: 70%
   :alt: Overview of Models and processes which are used by eGo
   :align: center


eTraGo's Theoretical Background
===============================

Learn more about eTraGo's theoretical background of methods and assumptions
`here <https://etrago.readthedocs.io/en/latest/theoretical_background.html>`_.

eDisGo's Theoretical Background
===============================

Learn more about eTraGo's theoretical background of methods and assumptions
`here <https://edisgo.readthedocs.io/en/latest/start_page.html>`_.


eDisGo Cluster Method
=====================

In order to achieve acceptable computation times, the problem's complexity can be reduced by applying a k-means cluster-algorithm to MV grids. The algorithm identifies a specified number of representative MV grids and assigns a weighting to each grid. As described `here <https://openego.readthedocs.io/en/dev/api/modules.html#edisgo>`_, the available clustering attributes are:

* The cumulative installed **wind capacity**,
* the cumulative installed **solar capacity**,
* the distance between transition point and **farthest node** of the MV grid and
* the installed **battery capacity** (as a results of eTraGo's investment optimization).

Subsequent to the MV grid simulations with the reduced number of representative grids, the cluster weighting is used to extrapolate the costs back to the original number of MV grids.


Economic calculation
====================

The tool *eGo* unites the extra high (ehv) and high voltage (hv) models with the 
medium (mv) and low voltage (lv) models to ascertain the costs per selected 
measure and scenario. This results in a cross-grid-level economic result of 
the electrical grid and storage optimisation.


Overnight costs
---------------

The *overnight costs* represents the investment costs of the components which 
appears for a given period *T* and a interest rate *p* of the optimisation. As
default *eGo* calculates with an interest rate ( *p* ) of ``0.05`` and a number 
of periods ( *T* ) of ``40 years``. The values are based on the [StromNEV_A1]_ 
for the grid investment regulation in Germany. 

The present value of an annuity (PVA) is calculated as:
            
.. math::
        PVA =   (1 / p) - (1 / (p*(1 + p)^T))

The period is given by the start and end time of a seleceted calculation and 
the year with ``8760 hours``. The overnight costs ( :math:`C_on` ) are
calculated as:

.. math::
        C_on = C_cc * PVA * (( T / ( period + 1 ))


Annuity costs
-------------

The *annuity costs* represents theoretical investment costs of an given period
of the optimisation which makes the different costs comparable.

The annuity costs ( :math:`C_a` )  is calculated as:

.. math::
        C_a = (C_on / ( PVA * ( year / ( period + 1))))


The capital costs ( *C_cc* ) of the gird measures (lines and transformer) are 
calculated as:

.. math::
        Line_cc = Extension [MVA] * capital costs [EUR/MVA] * Line length [km]    

.. math::
        Transformer_cc  = Extension [MVA] * capital costs [EUR/MVA]    


The conversion of the given annuity costs of *eTraGo* is done in
:func:`~ego.tools.economics.etrago_convert_overnight_cost`.


Investment costs ehv/hv
-----------------------

The investment costs of the grid and storage expantion are taken from the studies
[NEP2015a]_ for the extra and high voltage components and the [Dena]_. The 
given costs are transformed in respect to PyPSA *[€/MVA]* format [PyPSA]_ 
components for the optimisation.
    

**Overview of grid cost assumtions:**

The table displays the transformer and line costs which are used for the 
calculation with *eTraGo*.

.. csv-table:: Overview of grid cost assumtions
   :file: files/investment_costs_of_grid_ measures.csv
   :delim: ,
   :header-rows: 1

The *eTraGo* calculation of the annuity costs per simulation periode is defined 
in :func:`~etrago.tools.utilities.set_line_costs` and 
:func:`~etrago.tools.utilities.set_trafo_costs`. 

**Overview of storage cost assumtions:**

.. figure:: images/etrago-storage_parameters.png
   :scale: 80%
   :alt: Overview of eTraGo storage parameters and costs

Investment costs mv/lv
----------------------

The tool *eDisGO* is calculating all grid expansion measures as capital or 
*overnight* costs. In order to get the annuity costs of eDisGo's optimisation 
results the function :func:`~ego.tools.economics.edisgo_convert_capital_costs`
is used. The cost assumption of [eDisGo]_ are taken from the [Dena]_ 
and [CONSENTEC]_ study. Depents on the component the costs including earthwork 
costs depend on population density according to [Dena]_.



References
==========


.. [NEP2015a] Übertragungsnetzbetreiber Deutschland. (2015).
    *Netzentwicklungsplan Strom 2025 - Kostenschaetzungen*, Version 2015, 
    1. Entwurf, 2015. (`<https://www.netzentwicklungsplan.de/sites/default/files
    /paragraphs-files/kostenschaetzungen_nep_2025_1_entwurf.pdf>`_)

.. [Dena] dena Verteilnetzstudie. (2012).
    *Ausbau- und Innovationsbedarf der Stromverteilnetze in Deutschland bis 2030.*
    , Version 2015. (`<https://shop.dena.de/sortiment/detail/produkt/
    dena-verteilnetzstudie-ausbau-und-innovationsbedarf-der-stromverteilnetze-in-deutschland-bis-2030/>`_)

.. [PyPSA] PyPSA’s documentation (2018).
    *Documentation of components.* , Version v0.11.0. (`<https://pypsa.org/doc/components.html>`_)

.. [StromNEV_A1] Stromnetzentgeltverordnung - StromNEV Anlage 1 (2018).
    *Verordnung über die Entgelte für den Zugang zu Elektrizitätsversorgungsnetzen*
    *(Stromnetzentgeltverordnung - StromNEV) Anlage 1 (zu § 6 Abs. 5 Satz 1)*
    *Betriebsgewöhnliche Nutzungsdauern*.
    (`<https://www.gesetze-im-internet.de/stromnev/anlage_1.html>`_)

.. [Overnight cost] Wikipedia (2018).
    *Definition of overnight cost*. 
    (`<https://en.wikipedia.org/wiki/Overnight_cost>`_)

.. [eDisGo] eDisGo - grid expantion costs (2018).
    *Cost assumption on mv and lv grid components*. 
    (`<https://github.com/openego/eDisGo/blob/dev/edisgo/config/
    config_grid_expansion_default.cfg#L85-L107>`_)

.. [CONSENTEC] CONSENTEC et.al (2006).
    *Untersuchung der Voraussetzungen und möglicher Anwendung analytischer*
    *Kostenmodelle in der deutschen Energiewirtschaft *. 
    (`<https://www.bundesnetzagentur.de/SharedDocs/Downloads/DE/Sachgebiete/
    Energie/Unternehmen_Institutionen/Netzentgelte/Anreizregulierung/
    GA_AnalytischeKostenmodelle.pdf?__blob=publicationFile&v=1>`_)



