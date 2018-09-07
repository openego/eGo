# -*- coding: utf-8 -*-
# Copyright 2016-2018 Europa-Universität Flensburg,
# Flensburg University of Applied Sciences,
# Centre for Sustainable Energy Systems
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# File description
"""
This file contains all functions regarding the clustering of MV grids
"""
__copyright__ = ("Flensburg University of Applied Sciences, "
                 "Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc"

# Import
#from __future__ import print_function
import os
import logging

if not 'READTHEDOCS' in os.environ:
    import pickle
    
    import pandas as pd
    
    from sklearn.cluster import KMeans
    import numpy as np
    
logger = logging.getLogger(__name__)

def analyze_attributes(ding0_files):
    """
    Calculates the attributes wind and solar capacity and farthest node
    for all files in ding0_files. Results are written to ding0_files
    
    Parameters
    ----------
    ding0_files : :obj:`str`
        Path to ding0 files
        
    """
    base_path = ding0_files

    not_found = []
    tccs = []  # Total Cumulative Capacity of Solar
    tccw = []  # Total Cumulative Capacity of Wind
    fnlvmv = []  # the Farthest Node in both networks (lv and mv)
    MV_id_list = []  # Distrct id list

    for district_number in list(range(1, 4000)):

        try:
            pickle_name = 'ding0_grids__{}.pkl'.format(
                district_number)  
            nd = pickle.load(open(os.path.join(base_path, pickle_name), 'rb'))
            print('District no.', district_number, 'found!')
        except:
            not_found.append(district_number)
            continue

        MV_id = 0
        MV_id = nd._mv_grid_districts[0].id_db

        mv_cum_solar_MV = 0  # Solar cumulative capacity in MV
        mv_cum_wind_MV = 0  # Solar cumulative capacity in MV

        # cumulative capacity of solar and wind in MV
        for geno in nd._mv_grid_districts[0].mv_grid.generators():
            if geno.type == 'solar':
                mv_cum_solar_MV += geno.capacity
            if geno.type == 'wind':
                mv_cum_wind_MV += geno.capacity

        lvg = 0
        mv_cum_solar_LV = 0
        mv_cum_wind_LV = 0

        # cumulative capacity of solar and wind in LV
        for lvgs in nd._mv_grid_districts[0].lv_load_areas():
            for lvgs1 in lvgs.lv_grid_districts():
                lvg += len(list(lvgs1.lv_grid.generators()))
                for deno in lvgs1.lv_grid.generators():
                    if deno.type == 'solar':
                        mv_cum_solar_LV += deno.capacity
                    if deno.type == 'wind':
                        mv_cum_wind_LV += deno.capacity

        # Total solar cumulative capacity in lv and mv
        total_cum_solar = mv_cum_solar_MV + mv_cum_solar_LV
        # Total wind cumulative capacity in lv and mv
        total_cum_wind = mv_cum_wind_MV + mv_cum_wind_LV

        # append to lists
        tccs.append(total_cum_solar)
        tccw.append(total_cum_wind)

        # The farthest node length from MV substation
        from ding0.core.network.stations import LVStationDing0

        tot_dist = []
        max_length = 0
        max_length_list = []
        max_of_max = 0

        # make CB open (normal operation case)
        nd.control_circuit_breakers(mode='open')
        # setting the root to measure the path from
        root_mv = nd._mv_grid_districts[0].mv_grid.station()
        # 1st from MV substation to LV station node
        # Iteration through nodes
        for node2 in nd._mv_grid_districts[0].mv_grid._graph.nodes():
            # select only LV station nodes
            if isinstance(
                    node2, 
                    LVStationDing0) and not node2.lv_load_area.is_aggregated:

                length_from_MV_to_LV_station = 0
                # Distance from MV substation to LV station node
                length_from_MV_to_LV_station = nd._mv_grid_districts[
                        0
                        ].mv_grid.graph_path_length(
                    node_source=node2, node_target=root_mv) / 1000

                # Iteration through lv load areas
                for lvgs in nd._mv_grid_districts[0].lv_load_areas():
                    for lvgs1 in lvgs.lv_grid_districts():  
                        if lvgs1.lv_grid._station == node2:
                            root_lv = node2  # setting a new root
                            for node1 in lvgs1.lv_grid._graph.nodes():  

                                length_from_LV_staion_to_LV_node = 0
                                
                                # Distance from LV station to LV nodes
                                length_from_LV_staion_to_LV_node = (
                                        lvgs1.lv_grid.graph_path_length(
                                    node_source=node1, 
                                    node_target=root_lv) / 1000)

                                length_from_LV_node_to_MV_substation = 0
                                
                                # total distances in both grids MV and LV
                                length_from_LV_node_to_MV_substation = (
                                        length_from_MV_to_LV_station 
                                        + length_from_LV_staion_to_LV_node)

                                # append the total distance to a list
                                tot_dist.append(
                                    length_from_LV_node_to_MV_substation)
                            if any(tot_dist):  
                                max_length = max(tot_dist)
                                
                                # append max lengths of all grids to a list
                                max_length_list.append(max_length)
                    if any(max_length_list):  
                        # to pick up max of max
                        max_of_max = max(max_length_list)

        fnlvmv.append(max_of_max)  # append to a new list
        MV_id_list.append(MV_id)  # append the network id to a new list

    # export results to dataframes
    d = {'id': MV_id_list, 'Solar_cumulative_capacity': tccs,
         'Wind_cumulative_capacity': tccw,
         'The_Farthest_node': fnlvmv}  # assign lists to columns
    # not founded networks
    are_not_found = {'District_files_that_are_not_found': not_found}

    df = pd.DataFrame(d)  # dataframe for results

    # dataframe for not found files id
    df_are_not_found = pd.DataFrame(are_not_found)

    # Exporting dataframe to CSV files
    df.to_csv(base_path + '/' + 'attributes.csv', sep=',')
    df_are_not_found.to_csv(base_path + '/' + 'Not_found_grids.csv', sep=',')


def cluster_mv_grids(      
        no_grids,
        cluster_base):
    """
    Clusters the MV grids based on the attributes, for a given number
    of MV grids
    
    Parameters
    ----------
    ding0_files : :obj:`str`
        Path to ding0 files
    no_grids : int
        Desired number of clusters (of MV grids)
        
    Returns
    -------
    :pandas:`pandas.DataFrame<dataframe>`
        Dataframe containing the clustered MV grids and their weightings

    """
    cluster_base_pu = pd.DataFrame()
    
    for attribute in cluster_base:
        attribute_max = cluster_base[attribute].max()
        cluster_base_pu[attribute] = cluster_base[attribute] / attribute_max
          
    id_ = []
    m = []
    for idx, row in cluster_base_pu.iterrows():
        id_.append(idx)
        f = []
        for attribute in row:
            f.append(attribute)
            
        m.append(f)
        
    X = np.array(m)
    
    logger.info(
            'Used Clustering Attributes: \n {}'.format(
                    list(cluster_base.columns)))
        
    no_clusters = no_grids  
    
    ran_state = 1808

    # Starting KMeans clustering
    kmeans = KMeans(n_clusters=no_clusters, random_state=ran_state)

    # Return a label for each point 
    cluster_labels = kmeans.fit_predict(X)

    # Centers of clusters
    centroids = kmeans.cluster_centers_

    id_clus_dist = {}

    # Iterate through each point in dataset array X
    for i in range(len(X)):
        clus = cluster_labels[i]  # point's cluster id
        cent = centroids[cluster_labels[i]]  # Cluster's center coordinates

        # Distance from that point to cluster's center (3d coordinates)
        dist = (
                (X[i][0] - centroids[clus][0]) ** 2 
                + (X[i][1] - centroids[clus][1]) ** 2 
                + (X[i][2] - centroids[clus][2]) ** 2) ** (1 / 2)

        id_clus_dist.setdefault(clus, []).append({id_[i]: dist})
   
    cluster_df = pd.DataFrame(
            columns=[
            'no_of_points_per_cluster',
            'cluster_percentage',
            'the_selected_network_id',
            'represented_grids'])
    cluster_df.index.name = 'cluster_id'
   
    for key, value in id_clus_dist.items():
        no_points_clus = sum(1 for v in value if v)  
        # percentage of points per cluster
        clus_perc = (no_points_clus / len(X)) * 100

        id_dist = {}
        for value_1 in value:
            id_dist.update(value_1)

        # returns the shortest distance point (selected network) 
        short_dist_net_id_dist = min(id_dist.items(), key=lambda x: x[1])
        
        cluster_df.loc[key] = [
                no_points_clus,
                round(clus_perc, 2),
                short_dist_net_id_dist[0],
                list(id_dist.keys())]
        
    return cluster_df
