|readthedocs| |badge_githubstars| |zenodo|

-----


.. image:: https://openegoproject.files.wordpress.com/2017/02/open_ego_logo_breit.png?w=400
 

*A cross-grid-level electricity grid and storage optimization tool*
| `openegoproject.wordpress.com <https://openegoproject.wordpress.com/>`_


---
eGo
---

Integrated optimization of flexibility options and grid extension measures
for power grids based on `eTraGo <http://eTraGo.readthedocs.io/>`_ and
`eDisGo <http://edisgo.readthedocs.io/>`_. The Documentation of the eGo tool 
can be found on 
`openego.readthedocs.io <https://openego.readthedocs.io/>`_ .

.. contents::

------------
Installation
------------

.. code-block::


   $ pip3 install -e git+https://github.com/openego/PyPSA@master#egg=0.11.0fork 
   $ pip3 install eGo --process-dependency-links


----------------------------
Installing Developer Version
----------------------------

Create a virtualenvironment and activate it:

.. code-block::

   $ virtualenv venv --clear -p python3.5
   $ source venv/bin/activate
   $ cd venv
   $ pip3 install -e git+https://github.com/openego/eGo@dev#egg=eGo --process-dependency-links

-------
License
-------

© Europa-Universität Flensburg,
© Flensburg University of Applied Sciences,
*Centre for Sustainable Energy Systems*
© DLR Institute for Networked Energy Systems,
© Reiner-Lemoine-Institute"

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program. If not, see https://www.gnu.org/licenses/.



.. |badge_githubstars| image:: https://img.shields.io/github/stars/openego/eGo.svg?style=flat-square&label=github%20stars
    :target: https://github.com/openego/eGo/
    :alt: GitHub stars


.. |readthedocs| image:: https://readthedocs.org/projects/openego/badge/?version=master
    :target: http://openego.readthedocs.io/en/latest/?badge=master
    :alt: Documentation Status
    
.. |zenodo| image:: https://zenodo.org/badge/87306120.svg
    :target: https://zenodo.org/badge/latestdoi/87306120
