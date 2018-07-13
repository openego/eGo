#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 19 09:50:36 2018

@author: student
"""

from __future__ import print_function

import pickle
import os
import pandas as pd

from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm

def analyze_attributes(ding0_files):

    base_path = ding0_files
    
    not_found = []
    tccs = [] # Total Cumulative Capacity of Solar
    tccw = [] # Total Cumulative Capacity of Wind
    fnlvmv = [] # the Farthest Node in both networks (lv and mv)
    MV_id_list = [] # Distrct id list
    
    for district_number in list(range(1,4000)): # 3608 MVGDs
    
        # To bypass not found error
        try:
            pickle_name = 'ding0_grids__{}.pkl'.format(district_number) # To open the pickle files
            nd = pickle.load(open(os.path.join(base_path, pickle_name), 'rb')) # assign the data to a variable
            print('District no.', district_number, 'found!')
        except:
            not_found.append(district_number) # append not found network files id to a list
            #print('District no.', district_number, 'NOT found') # print not found ids
            continue
    
        MV_id = 0
        MV_id = nd._mv_grid_districts[0].id_db
    
        mv_cum_solar_MV = 0 # Solar cumulative capacity in MV
        mv_cum_wind_MV  = 0 # Solar cumulative capacity in MV
    
        # cumulative capacity of solar and wind in MV
        for geno in nd._mv_grid_districts[0].mv_grid.generators():
            if geno.type == 'solar':
                mv_cum_solar_MV += geno.capacity
            if geno.type == 'wind':
                mv_cum_wind_MV += geno.capacity
    
        lvg = 0
#        lvg_type = []
#        counter_lv = [{}]
        mv_cum_solar_LV = 0
        mv_cum_wind_LV = 0
    
        # cumulative capacity of solar and wind in LV
        for lvgs in nd._mv_grid_districts[0].lv_load_areas():
            for lvgs1 in lvgs.lv_grid_districts():
                lvg += len(list(lvgs1.lv_grid.generators())) # No. of DGs in lv
                for deno in lvgs1.lv_grid.generators():
                    if deno.type == 'solar':
                        mv_cum_solar_LV += deno.capacity
                    if deno.type == 'wind':
                        mv_cum_wind_LV += deno.capacity
    
        total_cum_solar = mv_cum_solar_MV + mv_cum_solar_LV # Total solar cumulative capacity in lv and mv
        total_cum_wind = mv_cum_wind_MV + mv_cum_wind_LV # Total wind cumulative capacity in lv and mv
    
        # append to lists
        tccs.append(total_cum_solar)
        tccw.append(total_cum_wind)
    
        # The farthest node length from MV substation
        from ding0.core.network.stations import LVStationDing0
    
        tot_dist = []
        max_length = 0
        max_length_list = []
        max_of_max = 0
    
        nd.control_circuit_breakers(mode='open') # make CB open (normal operation case)
        root_mv = nd._mv_grid_districts[0].mv_grid.station() # setting the root to measure the path from
        # 1st from MV substation to LV station node
        for node2 in nd._mv_grid_districts[0].mv_grid._graph.nodes(): # Iteration through nodes
            if isinstance(node2, LVStationDing0) and not node2.lv_load_area.is_aggregated: # select only LV station nodes
    
                length_from_MV_to_LV_station = 0
                # Distance from MV substation to LV station node
                length_from_MV_to_LV_station = nd._mv_grid_districts[0].mv_grid.graph_path_length(node_source=node2,node_target=root_mv) / 1000
                # 2nd from LV station node to the longest distance node
    
                for lvgs in nd._mv_grid_districts[0].lv_load_areas(): # Iteration through lv load areas
                    for lvgs1 in lvgs.lv_grid_districts(): # Iteration through lv grid districts
                        # In order to measure the distance between the LV station and the nodes that belong to it and not from other stations
                        if lvgs1.lv_grid._station == node2:
                            root_lv = node2 # setting a new root
                            for node1 in lvgs1.lv_grid._graph.nodes(): # iteration of all nodes in LV grid
    
                                    length_from_LV_staion_to_LV_node = 0
                                    # Distance from LV station to LV nodes
                                    length_from_LV_staion_to_LV_node = lvgs1.lv_grid.graph_path_length(node_source=node1,node_target=root_lv) / 1000
    
                                    length_from_LV_node_to_MV_substation = 0
                                    # total distances in both grids MV and LV
                                    length_from_LV_node_to_MV_substation = length_from_MV_to_LV_station + length_from_LV_staion_to_LV_node
    
                                    tot_dist.append(length_from_LV_node_to_MV_substation) # append the total distance to a list
                            if any(tot_dist): # to make sure the list is not empty
                                max_length = max(tot_dist) # to pick up the max length within this grid
                                max_length_list.append(max_length) # append max lengths of all grids to a list
                    if any(max_length_list): # to make sure the list is not empty
                        max_of_max = max(max_length_list) # to pick up max of max
    
        fnlvmv.append(max_of_max) # append to a new list
        MV_id_list.append(MV_id) # append the network id to a new list
    
    # export results to dataframes
    d = {'id': MV_id_list,'Solar_cumulative_capacity': tccs,
         'Wind_cumulative_capacity': tccw,
         'The_Farthest_node': fnlvmv} # assign lists to columns
    # not founded networks
    are_not_found = {'District_files_that_are_not_found': not_found}
    
    df = pd.DataFrame(d) # dataframe for results
    
    df_are_not_found = pd.DataFrame(are_not_found) # dataframe for not found files id
    
    # Exporting dataframe to CSV files
    df.to_csv(base_path + '/' + 'attributes.csv', sep=',')
    df_are_not_found.to_csv(base_path + '/' + 'Not_found_grids.csv', sep=',')
    
    ##3d scatter plotting
    #from mpl_toolkits.mplot3d import Axes3D
    #import matplotlib.pyplot as plt
    #
    #fig = plt.figure()
    #ax = fig.add_subplot(111, projection='3d')
    #
    #X = tccs
    #Y = tccw
    #Z = fnlvmv
    #
    #ax.scatter(X, Y, Z)
    #
    #ax.set_xlim(0, max(tccs)/1000)
    #ax.set_ylim(0, max(tccw)/1000)
    #ax.set_zlim(0, max(fnlvmv))
    #
    #ax.set_xlabel('\nSolar cumulative capacity (MW)', linespacing=2)
    #ax.set_ylabel('\nWind cumulative capacity (MW)', linespacing=2)
    #ax.set_zlabel('\nThe farthest node (km)', linespacing=2)
    #
    #plt.show()
    

def cluster_mv_grids(ding0_files, no_grids):
    
    # import CSV data file that exported from Networks_analysis_solar_wind_farthest-node.py and assign it to a data frame
    df = pd.read_csv(ding0_files + '/attributes.csv')
    
    # extract each column to a variable
    x = df.Solar_cumulative_capacity # Solar capacity in MV and LV
    y = df.Wind_cumulative_capacity # Wind capacity in MV and LV
    z = df.The_Farthest_node # The farthest node (the length between HV/MV substation to the farthest node in LV networks)
    id_ = df.id # Network id
    
    # Addressing the max value of each column
    max_solar = max(x)
    max_wind = max(y)
    max_farthest = max(z)
    
    # Converting data to perunit scale
    solar_pu = x / max_solar
    wind_pu = y / max_wind
    distances_pu = z / max_farthest
    
    # Converting from vectors to coordinates array
    m = []
    for r, s, t in zip(solar_pu, wind_pu, distances_pu):
        f = [r, s, t]
        m.append(f)
    X = np.array(m)
    
    # Initialize KMeans clustering by Sklearn pkg
    no_clusters = no_grids # no. of clusters
    
    # random state should be given in order to have same results with every run of the script
    # it acts as a seed where the algorihm define the starting clustering point, 1808 shows good results
    ran_state = 1808
    
    # Starting KMeans clustering
    kmeans = KMeans(n_clusters=no_clusters,random_state=ran_state)
    
    # Return a label for each point which indicates to which cluster each point is assigned
    cluster_labels = kmeans.fit_predict(X)
    
    # Centers of clusters
    centroids = kmeans.cluster_centers_
    
    id_clus_dist = {}
    
    # Iterate through each point in dataset array X
    for i in range(len(X)):
        clus = cluster_labels[i] # point's cluster id
        cent = centroids[cluster_labels[i]] # Cluster's center coordinates
    
        # Distance from that point to cluster's center (3d coordinates)
        dist = ((X[i][0] - centroids[clus][0]) ** 2 + (X[i][1] - centroids[clus][1]) ** 2 + (X[i][2] - centroids[clus][2]) ** 2) ** (1 / 2)
    
        # three results are appended to a list (cluster's id, point's (MVGD) id and distance from that point to cluster's center)
        #id_clus_dist = [clus, id_[i], dist]
        #list_id_clus_dist.append(id_clus_dist)
    
        # three results are appended to a dictionary (cluster's id, point's (MVGD) id and distance from that point to cluster's center)
        id_clus_dist.setdefault(clus, []).append({id_[i]: dist})
    
    cluster_id = []
    cluster_points = []
    clus_percentage = []
    closest_point = []
    
    #Iterating through the clusters dictionary (key represents cluster's id , value represents another disctionary with network's id and distance of that point to cluster's center)
    for key, value in id_clus_dist.items():
        no_points_clus = sum(1 for v in value if v) # How many points/cluster
        clus_perc = (no_points_clus / len(X)) * 100 # percentage of points per cluster
    
    # in the last dict "id_clus_dist" each key (cluster's id) has several dicts that contain information of network's id and distance,
    # the below code just to split the sub dicts and merge them as items in anothe single dict
        id_dist = {}
        for value_1 in value:
            id_dist.update(value_1)
    
        # returns the shortest distance point (selected network) to cluster's center
        short_dist_net_id_dist = min(id_dist.items(), key=lambda x: x[1])
    
        # Exporting CSV sheet for every cluster that contains the assigned points (networks) and siatance from each to cluster's center
        daf = pd.DataFrame()
        daf['Network_id'] = id_dist.keys()
        daf['Distance_to_cluster_center'] = id_dist.values()
#        daf.to_csv('Cluster_No_{}.csv'.format(key), sep=',')
    
        # export to lists
        cluster_id.append(key) # cluster id
        cluster_points.append(no_points_clus) # No of points / cluster
        clus_percentage.append(round(clus_perc,2))  # Percentage of points per cluster, # round(), two digits after comma
    
        # the nearest point to cluster center (represented network), there is [0] because it is a tuple
        closest_point.append(short_dist_net_id_dist[0])
    
    # exporting results to CSV file that contains cluster's id, the no. of assigned points (networks) and the selected network
    d = {'CLuster_id': cluster_id, 'no_of_points_per_cluster': cluster_points,
         'cluster_percentage': clus_percentage,
         'the_selected_network_id': closest_point}
    df = pd.DataFrame(d)
#    df.to_csv('Selected_networks_{}_clusters_dec.csv'.format(no_clusters), sep=',')
    
    return df
    
#    # Initiation of 3d graph for scattering plot
#    fig = plt.figure()
#    fig.suptitle('KMeans clustering', fontsize=20)
#    ax = fig.add_subplot(111, projection='3d')
#    
#    # 3d scatter Plot
#    colors = cm.spectral(cluster_labels.astype(float) / no_clusters)
#    ax.scatter(X[:, 0], X[:, 1], X[:, 2], alpha=0.3, c=colors)
#    
#    # Clusters centers 3d scatter plot
#    ax.scatter(centroids[:, 0], centroids[:, 1], centroids[:, 2], marker='x', alpha=1, s=50, linewidths=5, zorder=10,c='r')
#    
#    #limiting the axes scale
#    ax.set_xlim(0, 1)
#    ax.set_ylim(0, 1)
#    ax.set_zlim(0, 1)
#    
#    # show 3d scatter clustering
#    plt.show()
#    
#    # as for this example where no. of clusters is 20, the results should show 21 CSV files (20 for clusters and 1 for the selected netorks)