============
Installation
============
eGo is designed as a Python package therefore it is mandatory to have
`Python 3 <https://www.python.org/downloads/.>`_ installed. If you have a
working Python3 environment, use PyPI to install the latest eGo version.
We highly recommend to use a virtual environment. Use the following pip
command in order to install eGo:

.. code-block:: bash

  $ pip3 install eGo --process-dependency-links

Please ensure, that you are using the pip version 18.1.
Use ``pip install --upgrade pip==18.1`` to get the right pip version.
In Case of problems with the Installation and the ``dependency_links`` of
the PyPSA fork, please istall PyPSA from the github.com/openego Repository.

.. code-block:: bash

  $ pip3 install -e git+https://github.com/openego/PyPSA@master#egg=0.11.0fork


Using virtual environment
=========================

At first create a virtual environment and activate it:

.. code-block:: bash

   $ virtualenv venv --clear -p python3.5
   $ source venv/bin/activate
   $ cd venv

Inside your virtual environment you can install eGo with the pip command.

Linux and Ubuntu
================

The package eGo is tested with Ubuntu 16.04 and 18.04 inside a virtual
environment of `virtualenv <https://virtualenv.pypa.io/en/stable/>`_.
The installation is shown above.



Windows or Mac OSX users
========================

For Windows and/or Mac OSX user we highly recommend to install and use Anaconda
for your Python3 installation. First install anaconda including python version 3.5 or
higher from https://www.anaconda.com/download/ and open an anaconda
prompt as administrator and run:

.. code-block:: bash

  $ conda install pip
  $ conda config --add channels conda-forge
  $ conda install shapely
  $ pip3 install eGo --process-dependency-links

The full documentation can be found
`on this page <https://docs.anaconda.com/anaconda/install/>`_. We use Anaconda
with an own environment in order to reduce problems with packages and different
versions on our system. Learn more about
`Anacona <https://conda.io/docs/user-guide/tasks/manage-environments.html>`_
environments.



