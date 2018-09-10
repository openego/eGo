# -*- coding: utf-8 -*-
import os
from setuptools import find_packages, setup

__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc"

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='eGo',
    version='0.3.0',
    author='wolfbunke, maltesc',
    author_email='wolf-dieter.bunke@uni-flensburg.de',
    description=("A cross-grid-level electricity grid and storage "
                   "optimization tool "),
    long_description= read('README.rst'),
    url='https://github.com/openego/eGo',
    license="GNU Affero General Public License Version 3 (AGPL-3.0)",
    packages=find_packages(),
    package_dir={'ego': 'ego'},
    include_package_data=True,
    install_requires=['egoio == 0.4.5',
                      'scikit-learn == 0.19.0',
                      'pandas >= 0.19.0, <=0.20.3',
                      'pypsa==0.11.0fork',
                      'sqlalchemy >= 1.0.15, <= 1.1.4',
                      'geoalchemy2 >= 0.3.0, <=0.4.0',
                      'matplotlib >= 1.5.3, <=1.5.3',
                      'tsam==0.9.9',
                      'shapely',
                      'oedialect'],
    dependency_links=[
        ('git+https://git@github.com/openego/PyPSA.git'
         '@master#egg=pypsa-0.11.0fork')],
    extras_require={
        'doc': [
            'sphinx >= 1.4',
            'sphinx_rtd_theme',
            'sphinxcontrib-httpdomain']},
    package_data={
        'ego': [os.path.join('tools', '*.csv')],
        'ego': [os.path.join('tools', '*.json')],
        'ego': [os.path.join('', '*.json')],
        'ego.data': ['*.csv']
    }
    )
    
  
