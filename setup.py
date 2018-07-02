import os
from setuptools import find_packages, setup

__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke"

setup(name='eGo',
      author='wolfbunke, maltesc',
      author_email='',
      description=("A python package for distribution and transmission"
                   "grid analysis and optimization based eDisGo and eTraGo"),
      version='0.2',
      url='https://github.com/openego/eGo',
      license="GNU Affero General Public License Version 3 (AGPL-3.0)",
      packages=find_packages(),
      include_package_data=True,
      install_requires=['egoio == 0.4.1',
                        'eDisGo == 0.0.2',
                        'eTraGo ==  0.6',
                        'pandas ==0.20.3',
                        'pypsa==0.11.0fork',
                        'sqlalchemy >= 1.0.15, <= 1.2.0',
                        'geoalchemy2 >= 0.3.0, <=0.4.0',
                        'pyproj == 1.9.5.1',
                        'geopandas==0.3.0',
                        'Rtree==0.8.3',
                        'plotly==2.2.3',
                        'matplotlib >= 1.5.3, <=1.5.3'],
      dependency_links=[('git+https://git@github.com/openego/PyPSA.git'
                         '@dev#egg=pypsa-0.11.0fork'),
                        ('git+https://git@github.com:python-visualization/'
                         'folium.git@dev#egg=folium')
                        ],
      extras_require={
          'docs': [
              'sphinx >= 1.4',
              'sphinx_rtd_theme',
              'sphinxcontrib-httpdomain']},
      package_data={
          'ego': [
              os.path.join('*.json'),
              os.path.join('tools', '*.json'),
              os.path.join('data', '*.csv')]
      }
      )
