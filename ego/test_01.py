#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 12:39:24 2017

@author: student
"""

#%% Package Import and Options
import sys
print ("Python version: " + sys.version + "\n")

import os # Operation system
print ("WD: " + os.getcwd() + "\n")



    # eTraGo
from etrago.appl import etrago # This is the main function of etrago.
        # The import function 

    # eGo Subpackages
from tools.plots import (make_all_plots,plot_line_loading, plot_stacked_gen,
                                     add_coordinates, curtailment, gen_dist,
                                     storage_distribution)
from tools.utilities import get_scenario_setting


#%% Data Import

    # Import scenario settings **kwargs of eTraGo
args = get_scenario_setting() # Gets scenario settings form json file.

print ("eTraGo Input Parameters: \n")

for x in args:
    print (x)
    for y in args[x]:
        print (y,':',args[x][y]) # Mehrdimensionales Dictionary

print("Reproduce Noise: " + str(args['eTraGo_args']['reproduce_noise'])) # simply test for accessing dictionary entries... 
 
     
#%% Data Optimization, Prozessing

    # Start eTraGo calculation
eTraGo_network = etrago(args['eTraGo_args']) # Baut über oemof.de (und config.ini eine Verbindung zur Datenbank auf)


#%% Plotting

    # Plot everything to console
make_all_plots(eTraGo_network) # Line loading, commitment, storage



