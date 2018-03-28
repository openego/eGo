.. image:: https://readthedocs.org/projects/openego/badge/?version=latest
    :target: http://openego.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://openegoproject.files.wordpress.com/2017/02/open_ego_logo_breit.png?w=400

eGo
======

Integrated optimization of flexibility options and grid extension measures for power grids based on eTraGo and eDisGo.

A speciality in this context is that transmission grids are described by the 380, 220 and 110 kV in Germany. The integration of the transmission grid (via eTraGo) and distribution grid (via eDisGo) is part of eGo.

.. contents::

Installing Developer Version
============================

Create a virtualenvironment (where you like it) and activate it:

.. code-block::

   $ virtualenv eGo --clear -p python3.5
   $ source venv/bin/activate

   $ pip install -e git+https://github.com/openego/eGo@dev#egg=eGo --process-dependency-links --allow-all-external


Copyleft
========

Code licensed under "GNU Affero General Public License Version 3 (AGPL-3.0)"
It is a collaborative work with several copyright owner:
Cite as "eGo" © Flensburg University of Applied Sciences, Centre for Sustainable Energy Systems © Europa-Universität Flensburg, Centre for Sustainable Energy Systems © DLR Institute for Networked Energy Systems, © Reiner-Lemoine-Institute"
