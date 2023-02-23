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
__copyright__ = (
    "Flensburg University of Applied Sciences, "
    "Europa-Universität Flensburg, "
    "Centre for Sustainable Energy Systems"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc, mltja"

import logging
import os

if "READTHEDOCS" not in os.environ:
    import numpy as np
    import pandas as pd

    from sklearn.cluster import KMeans

    import ego.mv_clustering.egon_data_io as db_io

    from ego.mv_clustering.database import (
        get_engine,
        register_tables_in_saio,
        sshtunnel,
    )

logger = logging.getLogger(__name__)


def cluster_attributes_to_csv(attributes_path, config=None):
    """
    Calculates the attributes to cluster

    Parameters
    ----------
    attributes_path : :obj:`str`
        Path to attributes csv

    config : :obj:`dict`
        Config dict.

    """

    with sshtunnel(config=config):
        engine = get_engine(config=config)
        orm = register_tables_in_saio(engine, config=config)

        grid_ids_df = db_io.get_grid_ids(engine=engine, orm=orm)
        solar_capacity_df = db_io.get_solar_capacity(engine=engine, orm=orm)
        wind_capacity_df = db_io.get_wind_capacity(engine=engine, orm=orm)
        emobility_capacity_df = db_io.get_emobility_capacity(engine=engine, orm=orm)

    df = pd.concat(
        [grid_ids_df, solar_capacity_df, wind_capacity_df, emobility_capacity_df],
        axis="columns",
    )
    df.fillna(0, inplace=True)

    df.to_csv(attributes_path)


def mv_grid_clustering(data_df, working_grids=None, config=None):
    """
    Clusters the MV grids based on the attributes, for a given number
    of MV grids

    Parameters
    ----------
    n_cluster : int
        Desired number of clusters (of MV grids)

    Returns
    -------
    :pandas:`pandas.DataFrame<dataframe>`
        Dataframe containing the clustered MV grids and their weightings

    """
    random_seed = config["eGo"]["random_seed"]
    n_clusters = config["eDisGo"]["n_clusters"]

    # Norm attributes
    for attribute in data_df:
        attribute_max = data_df[attribute].max()
        data_df[attribute] = data_df[attribute] / attribute_max

    # Starting KMeans clustering
    logger.info(f"Used Clustering Attributes: {data_df.columns.to_list()}")
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_seed)
    data_array = data_df.to_numpy()
    labels = kmeans.fit_predict(data_array)
    centroids = kmeans.cluster_centers_

    result_df = pd.DataFrame(index=data_df.index)
    result_df["label"] = labels
    # For each sample, calculate the distance to its assigned centroid.
    result_df["centroid_distance"] = np.linalg.norm(
        data_array - centroids[labels], axis=1
    )
    result_df["representative"] = False

    if working_grids is None:
        result_df["working"] = True
    else:
        result_df["working"] = result_df.join(working_grids).fillna(False)["working"]

    failing_labels = []
    for label in np.unique(labels):
        try:
            rep = result_df.loc[
                result_df["working"] & (result_df["label"] == label),
                "centroid_distance",
            ].idxmin()
            result_df.loc[rep, "representative"] = True
        except ValueError:
            failing_labels.append(label)

    n_grids = result_df.shape[0]
    df_data = []
    columns = [
        "representative",
        "n_grids_per_cluster",
        "relative_representation",
        "represented_grids",
    ]
    for label in np.unique(labels):
        represented_grids = result_df[result_df["label"] == label].index.to_list()
        n_grids_per_cluster = len(represented_grids)
        relative_representation = (n_grids_per_cluster / n_grids) * 100
        try:
            representative = result_df[
                result_df["representative"] & (result_df["label"] == label)
            ].index.values[0]
        except IndexError:
            representative = False

        row = [
            representative,
            n_grids_per_cluster,
            relative_representation,
            represented_grids,
        ]
        df_data.append(row)

    cluster_df = pd.DataFrame(df_data, index=np.unique(labels), columns=columns)
    cluster_df.index.name = "cluster_id"

    return cluster_df


def cluster_workflow(config=None):
    attributes_path = os.path.join(config["eDisGo"]["grid_path"], "attributes.csv")
    working_grids_path = os.path.join(
        config["eDisGo"]["grid_path"], "working_grids.csv"
    )

    if not os.path.isfile(attributes_path):
        logger.info("Attributes file is missing, get attributes from egon-data.")
        cluster_attributes_to_csv(attributes_path=attributes_path, config=config)

    data_to_cluster = pd.read_csv(attributes_path, index_col=0)[
        config["eDisGo"]["cluster_attributes"]
    ]
    if os.path.isfile(working_grids_path):
        working_grids = pd.read_csv(working_grids_path, index_col=0)
    else:
        logger.info("'working_grids.csv' is missing, select representative grids.")
        working_grids = None

    return mv_grid_clustering(
        data_to_cluster, working_grids=working_grids, config=config
    )
