#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is the cluster testfile
"""

import os
import json
from tools.io import eGo
from tools.utilities import define_logging

logger = define_logging(name='ego')

settings_dir = 'settings'
if not os.path.exists(settings_dir):
    os.makedirs(settings_dir)
            
jsonfile='scenario_setting (cluster).json'

with open(jsonfile) as fp:
    json_data = json.load(fp)
 
for no_grids in range(1280,3600,5):
    
    json_data['eDisGo']['no_grids'] = no_grids
    json_data['eDisGo']['results'] = 'cluster_results/' + str(no_grids)
   

    new_jsonpath = os.path.join(settings_dir, str(no_grids) + '.json')

    with open(new_jsonpath, 'w') as fp:
        json.dump(json_data, fp)  
        
    eGo(jsonpath=new_jsonpath)



