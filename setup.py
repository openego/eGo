# -*- coding: utf-8 -*-
import os
from setuptools import find_packages, setup
from pip._internal.req import parse_requirements

__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc"

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


req = [
    'egoio==0.4.5',
    'ding0==v0.1.9',
    'pycallgraph',
    'eDisGo==v0.0.9',
    'eTraGo==0.7.1',
    'scikit-learn==0.19.0',
    'pandas==0.20.3',
    'pypsa==0.11.0fork',
    'sqlalchemy==1.2.0',
    'geoalchemy2 >= 0.3.0, <= 0.4.0',
    'tsam==0.9.9',
    'geopandas',
    'matplotlib==3.0.0',
    'Rtree',
    'descartes',
    'pyproj',
    'plotly==2.2.3',
    'shapely',
    'multiprocess',
    'folium',
    'oedialect',
]

dev_req = [
    "pre-commit",
    "black",
    "isort",
    "pyupgrade",
    "flake8",
]

doc_req = [
    'sphinx >= 1.4',
    'sphinx_rtd_theme',
    'sphinxcontrib-httpdomain',
    'numpydoc == 0.7.0',
    'aiohttp_jinja2',
    'sphinx-jsondomain',
]

full_req = list(set(dev_req + doc_req))

extras = {
    "dev": dev_req,
    "doc": doc_req,
    "full": full_req,
}
   

setup(
    name='eGo',
    version='0.3.4',
    author='wolfbunke, maltesc',
    author_email='wolf-dieter.bunke@uni-flensburg.de',
    description=("A cross-grid-level electricity grid and storage "
                   "optimization tool "),
    long_description=read('README.rst'),
    url='https://github.com/openego/eGo',
    license="GNU Affero General Public License Version 3 (AGPL-3.0)",
    packages=find_packages(),
    package_dir={'ego': 'ego'},
    include_package_data=True,
    install_requires=req,
    dependency_links=[
        ('git+https://git@github.com/openego/PyPSA.git'
         '@master#egg=pypsa-0.11.0fork')],
    extras_require=extras,
    package_data={
        'ego': [os.path.join('tools', '*.csv')],
        'ego': [os.path.join('tools', '*.json')],
        'ego': [os.path.join('', '*.json')],
        'ego.data': ['*.csv']
    }
    )

