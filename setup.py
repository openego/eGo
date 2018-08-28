import os
from setuptools import find_packages, setup

__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='eGo',
      version='0.3.0dev',
      author='wolfbunke, maltesc',
      author_email='',
      description=("A python package for distribution and transmission"
                   "grid analysis and optimization based eDisGo and eTraGo"),
      long_description=read('README.rst'),
      long_description_content_type="text/x-rst",
      url='https://github.com/openego/eGo',
      license="GNU Affero General Public License Version 3 (AGPL-3.0)",
      packages=find_packages(),
      package_dir={'ego': 'ego'},
      include_package_data=True,
      install_requires=['egoio==0.4.0',
                        'eDisGo==0.0.6dev',
                        'eTraGo==0.6.1',
                        'pandas==0.20.3',
                        'pypsa==0.11.0fork',
                        'geoalchemy2>= 0.3.0, <=0.4.0',
                        'pyproj==1.9.5.1',
                        'geopandas',
                        'matplotlib>= 1.5.3, <=1.5.3',
                        'Rtree',
                        'descartes',
                        'plotly==2.2.3',
                        'Pyomo==5.5.0',
                        'oedialect',
                        'multiprocess',
                        'folium'
                        ],
      dependency_links=[('git+https://git@github.com/openego/PyPSA.git'
                         '@dev#egg=pypsa-0.11.0fork'),
                        ('git+https://git@github.com/openego/eDisGo.git'
                         '@dev#egg=0.0.6dev'),
                        ('git+https://git@github.com/openego/eTraGo.git'
                         '@dev#egg=0.6.1'),
                        ('git+https://git@github.com/openego/ego.io.git'
                         '@dev#egg=0.4.0')
                        ],
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
      },
      )
