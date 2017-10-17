#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 13:03:44 2017

@author: student
"""

print ("This is my eDisGo test file! \n")

#%% Package Import and Options
import sys
print ("Python version: " + sys.version + "\n")

import os # Operation system
print ("WD: " + os.getcwd() + "\n")

import pandas as pd
print ("Pandas Version: " + pd.__version__ + " (0.20.3 is for eDisGo, 0.19.1 for eTraGo)")

