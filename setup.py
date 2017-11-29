__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität Flensburg, Centre for Sustainable Energy Systems, Next Energy, "
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke"


from setuptools import find_packages, setup

setup(name='eGo',
      author='ZNES Flensburg',
      author_email='',
      description='Overall economic terms of electrical Transmission Grid Optimization and Distribution Grids of flexibility options for transmission grids based on PyPSA',
      version='0.0.1',
	  url='https://github.com/openego/eGo',
      license="GNU Affero General Public License Version 3 (AGPL-3.0)",
      packages=find_packages(),
      include_package_data=True,
      install_requires=['egoio == 0.2.11',
                        'egopowerflow == 0.0.4',
                        'pandas >= 0.17.0, <=0.19.1',
                        'sqlalchemy >= 1.0.15, <= 1.1.4',
                        'oemof.db >=0.0.4, <=0.0.4',
                        'geoalchemy2 >= 0.3.0, <=0.4.0',
'matplotlib >= 1.5.3, <=1.5.3'],
	dependency_links=['git+ssh://git@github.com/openego/eTraGo.git@dev#egg=eTraGo',
	'git+ssh://git@github.com/openego/PyPSA.git@dev#egg=PyPSA'],
	 extras_require={
        'docs': [
            'sphinx >= 1.4',
            'sphinx_rtd_theme']}
     )
