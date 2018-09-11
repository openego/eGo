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


requirements = parse_requirements("ego_dependencies.txt", session="")

setup(
    name='eGo',
    version='0.3.0.24',
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
    install_requires=[str(b.req) for b in requirements],
    dependency_links=[str(c._link) for c in requirements if c._link],
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
    
  
