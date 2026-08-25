============
Installation
============

eGo is an open-source Python package. The latest eGo release is quite old
and might no longer work. Therefore, the developer version should be used.

Python 3.10 is recommended for the developer installation. We highly
recommend using a virtual environment.


Prerequisites
=============

For the recommended installation, Git, Python 3.10, pip, and virtualenv
must be available on the system.

On the tested Ubuntu 26.04 LTS system, the required packages were installed
using:

.. code-block:: bash

   $ sudo apt-get install python3-pip
   $ sudo apt install git
   $ sudo add-apt-repository ppa:deadsnakes/ppa
   $ sudo apt install python3.10
   $ sudo apt install python3-virtualenv

The commands required to install these prerequisites may differ between
operating systems and Linux distributions.


Installing the developer version
================================

Create and activate a virtual environment:

.. code-block:: bash

   $ virtualenv venv --clear -p python3.10
   $ source venv/bin/activate

Clone the eGo repository and navigate to the repository directory:

.. code-block:: bash

   $ git clone https://github.com/openego/eGo.git
   $ cd eGo

Install eGo with all optional dependencies and activate the pre-commit hooks:

.. code-block:: bash

   $ python -m pip install -e .[full]
   $ pre-commit install

Dependency resolution may take some time. Messages stating that pip is
looking at multiple package versions do not necessarily indicate an
installation error.


Verifying the installation
==========================

The installation can be verified by importing eGo:

.. code-block:: bash

   $ python -c "import ego; print('eGo import successful')"

A successful installation produces the following output:

.. code-block:: text

   eGo import successful


Tested environment
==================

The developer installation was successfully tested with Python 3.10.21 on
Ubuntu 26.04 LTS in a virtual environment. Other Python versions and operating
systems may also work but were not evaluated during this installation test.


Windows or Mac OSX users
========================

For Windows and/or Mac OSX user we highly recommend to install and use Anaconda
for your Python3 installation. First install anaconda including python version 3.10 or
higher from https://www.anaconda.com/download/ and open an anaconda
prompt as administrator and run:

.. code-block:: bash

  $ conda install pip
  $ conda config --add channels conda-forge
  $ conda install shapely
  $ pip3 install eGo 

The full documentation can be found
`on this page <https://docs.anaconda.com/anaconda/install/>`_. We use Anaconda
with an own environment in order to reduce problems with packages and different
versions on our system. Learn more about
`Anacona <https://conda.io/docs/user-guide/tasks/manage-environments.html>`_
environments.



