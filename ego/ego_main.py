"""
Main script of eGo



"""

__copyright__ = "tba"
__license__ = "tba"
__author__ = "tba"

import sys
sys.path.append('/home/dozeumbuw/Dokumente/ZNES/open_eGo/Coding/eTraGo/eTraGo/')
from appl import etrago

#from eDisGo import ...

# define scenario (args)
args = {'network_clustering':False,
        'db': 'oedb2', # db session
        'gridversion':None, #None for model_draft or Version number (e.g. v0.2.10) for grid schema
        'method': 'lopf', # lopf or pf
        'start_h': 2301,
        'end_h' : 2312,
        'scn_name': 'SH Status Quo',
        'ormcls_prefix': 'EgoGridPfHv', #if gridversion:'version-number' then 'EgoPfHv', if gridversion:None then 'EgoGridPfHv'
        'outfile': '/path', # state if and where you want to save pyomo's lp file
        'results': '/path', # state if and where you want to save results as csv
        'solver': 'gurobi', #glpk, cplex or gurobi
        'branch_capacity_factor': 1, #to globally extend or lower branch capacities
        'storage_extendable':True,
        'load_shedding':True,
        'generator_noise':False}

# start calculations (eTraGo and eDisGo)
# rename resulting network container to eTraGo_network
eTraGo_network = etrago(args)
# eDisGo_network = edisgo()


# calculate power plant dispatch without grid utilization (either in pypsa or in renpassgis)

# result queries...call functions from utilities

## total system costs of transmission grid vs. total system costs of all distribution grids results in overall total
## details on total system costs:
## existing plants: usage, costs for each technology
## newly installed plants (storages, grid measures) with size, location, usage, costs
## grid losses: amount and costs

# possible aggregation of results

# exports: total system costs, plots, csv export files
