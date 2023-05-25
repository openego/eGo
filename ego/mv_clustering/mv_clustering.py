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


def get_cluster_attributes(attributes_path, scenario, config=None):
    """
    Determines attributes to cluster MV grids by.

    Considered attributes are PV, wind onshore and PtH capacity, as well as
    maximum load of EVs (in case of uncoordinated charging). All attributes are given
    in MW as well as in MW per km^2.

    Data is written to csv file and returned.

    Parameters
    ----------
    attributes_path : str
        Path to save attributes csv to, including the file name.
    scenario : str
        Scenario to determine attributes for. Possible options are "status_quo",
        "eGon2035", and "eGon100RE".
    config : dict
        Config dict.

    Returns
    -------
    pandas.DataFrame
        DataFrame with grid ID in index and corresponding attributes in columns:
        * "area" : area of MV grid in m^2
        * "pv_capacity_mw" : PV capacity in MW
        * "pv_capacity_mw_per_km2" : PV capacity in MW per km^2
        * "pv_capacity_expansion_mw" : PV expansion from status quo to given
            scenario in MW
        * "pv_capacity_expansion_mw_per_km2" : PV expansion from status quo to given
            scenario in MW per km^2
        * "wind_capacity_mw" : wind onshore capacity in MW
        * "wind_capacity_mw_per_km2" : wind onshore capacity in MW per km^2
        * "wind_capacity_expansion_mw" : wind onshore expansion from status quo to given
            scenario in MW
        * "wind_capacity_expansion_mw_per_km2" : wind onshore expansion from status quo
            to given scenario in MW per km^2
        * "electromobility_max_load_mw" : maximum load of EVs (in case of
            uncoordinated charging) in MW
        * "electromobility_max_load_mw_per_km2" : maximum load of EVs (in case of
            uncoordinated charging) in MW per km^2
        * "electromobility_max_load_expansion_mw" : increase in maximum load of EVs
            from status quo to given scenario (in case of uncoordinated charging) in MW
        * "electromobility_max_load_expansion_mw_per_km2" : increase in maximum load of
            EVs from status quo to given scenario (in case of uncoordinated charging)
            in MW per km^2
        * "pth_capacity_mw" : PtH capacity (for individual and district
            heating) in MW
        * "pth_capacity_mw_per_km2" : PtH capacity (for individual and
            district heating) in MW per km^2
        * "pth_capacity_expansion_mw" : increase in PtH capacity (for individual and
            district heating) from status quo to given scenario in MW
        * "pth_capacity_expansion_mw_per_km2" : increase in PtH capacity (for individual
            and district heating) from status quo to given scenario in MW per km^2

    """
    # get attributes from database
    with sshtunnel(config=config):
        engine = get_engine(config=config)
        orm = register_tables_in_saio(engine, config=config)

        grid_ids_df = db_io.get_grid_ids(engine=engine, orm=orm)
        solar_capacity_df = db_io.get_solar_capacity(
            scenario, grid_ids_df.index, orm, engine=engine
        )
        if scenario == "status_quo":
            solar_capacity_sq_df = solar_capacity_df
        else:
            solar_capacity_sq_df = db_io.get_solar_capacity(
                "status_quo", grid_ids_df.index, orm, engine=engine
            )
        wind_capacity_df = db_io.get_wind_capacity(
            scenario, grid_ids_df.index, orm, engine=engine
        )
        if scenario == "status_quo":
            wind_capacity_sq_df = wind_capacity_df
        else:
            wind_capacity_sq_df = db_io.get_wind_capacity(
                "status_quo", grid_ids_df.index, orm, engine=engine
            )
        emob_capacity_df = db_io.get_electromobility_maximum_load(
            scenario, grid_ids_df.index, orm, engine=engine
        )
        if scenario == "status_quo":
            emob_capacity_sq_df = emob_capacity_df
        else:
            emob_capacity_sq_df = db_io.get_electromobility_maximum_load(
                "status_quo", grid_ids_df.index, orm, engine=engine
            )
        pth_capacity_df = db_io.get_pth_capacity(
            scenario, grid_ids_df.index, orm, engine=engine
        )
        if scenario == "status_quo":
            pth_capacity_sq_df = pth_capacity_df
        else:
            pth_capacity_sq_df = db_io.get_pth_capacity(
                "status_quo", grid_ids_df.index, orm, engine=engine
            )
    emob_rename_col = "electromobility_max_load_expansion_mw"
    df = pd.concat(
        [
            grid_ids_df,
            solar_capacity_df,
            wind_capacity_df,
            emob_capacity_df,
            pth_capacity_df,
            solar_capacity_sq_df.rename(
                columns={"pv_capacity_mw": "pv_capacity_expansion_mw"}
            ),
            wind_capacity_sq_df.rename(
                columns={"wind_capacity_mw": "wind_capacity_expansion_mw"}
            ),
            emob_capacity_sq_df.rename(
                columns={"electromobility_max_load_mw": emob_rename_col}
            ),
            pth_capacity_sq_df.rename(
                columns={"pth_capacity_mw": "pth_capacity_expansion_mw"}
            ),
        ],
        axis="columns",
    ).fillna(0)

    # calculate expansion values
    df["pv_capacity_expansion_mw"] = (
        df["pv_capacity_mw"] - df["pv_capacity_expansion_mw"]
    )
    df["wind_capacity_expansion_mw"] = (
        df["wind_capacity_mw"] - df["wind_capacity_expansion_mw"]
    )
    df["electromobility_max_load_expansion_mw"] = (
        df["electromobility_max_load_mw"] - df["electromobility_max_load_expansion_mw"]
    )
    df["pth_capacity_expansion_mw"] = (
        df["pth_capacity_mw"] - df["pth_capacity_expansion_mw"]
    )

    # calculate relative values
    df["pv_capacity_mw_per_km2"] = df["pv_capacity_mw"] / (df["area_m2"] / 1e6)
    df["wind_capacity_mw_per_km2"] = df["wind_capacity_mw"] / (df["area_m2"] / 1e6)
    df["electromobility_max_load_mw_per_km2"] = df["electromobility_max_load_mw"] / (
        df["area_m2"] / 1e6
    )
    df["pth_capacity_mw_per_km2"] = df["pth_capacity_mw"] / (df["area_m2"] / 1e6)
    df["pv_capacity_expansion_mw_per_km2"] = df["pv_capacity_expansion_mw"] / (
        df["area_m2"] / 1e6
    )
    df["wind_capacity_expansion_mw_per_km2"] = df["wind_capacity_expansion_mw"] / (
        df["area_m2"] / 1e6
    )
    df["electromobility_max_load_expansion_mw_per_km2"] = df[
        "electromobility_max_load_expansion_mw"
    ] / (df["area_m2"] / 1e6)
    df["pth_capacity_expansion_mw_per_km2"] = df["pth_capacity_expansion_mw"] / (
        df["area_m2"] / 1e6
    )

    # write to csv
    df.to_csv(attributes_path)
    return df


def mv_grid_clustering(cluster_attributes_df, working_grids=None, config=None):
    """
    Clusters the MV grids based on the attributes, for a given number of MV grids.

    Parameters
    ----------
    cluster_attributes_df : pandas.DataFrame
        Dataframe with data to cluster grids by. Columns contain the attributes to
        cluster and index contains the MV grid IDs.
    working_grids : pandas.DataFrame
        DataFrame with information on whether MV grid can be used for calculations.
        Index of the dataframe contains the MV grid ID and boolean value in column
        "working" specifies whether respective grid can be used.
    config : dict
        Config dict.

    Returns
    -------
    pandas.DataFrame
        Dataframe containing the clustered MV grids and their weightings

    """
    random_seed = config["eGo"]["random_seed"]
    n_clusters = config["eDisGo"]["n_clusters"]

    # Norm attributes
    for attribute in cluster_attributes_df:
        attribute_max = cluster_attributes_df[attribute].max()
        cluster_attributes_df[attribute] = (
            cluster_attributes_df[attribute] / attribute_max
        )

    # Starting KMeans clustering
    logger.info(
        f"Used clustering attributes: {cluster_attributes_df.columns.to_list()}"
    )
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_seed)
    data_array = cluster_attributes_df.to_numpy()
    labels = kmeans.fit_predict(data_array)
    centroids = kmeans.cluster_centers_

    result_df = pd.DataFrame(index=cluster_attributes_df.index)
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
            rep_orig = result_df.loc[
                result_df["label"] == label, "centroid_distance"
            ].idxmin()
            result_df.loc[rep, "representative"] = True
            result_df.loc[rep, "representative_orig"] = rep_orig
        except ValueError:
            failing_labels.append(label)

    if len(failing_labels) > 0:
        logger.warning(
            f"There are {len(failing_labels)} clusters for which no representative "
            f"could be determined."
        )

    n_grids = result_df.shape[0]
    df_data = []
    columns = [
        "representative",
        "n_grids_per_cluster",
        "relative_representation",
        "represented_grids",
        "representative_orig",
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
        try:
            representative_orig = result_df[
                result_df["representative"] & (result_df["label"] == label)
            ].representative_orig.values[0]
            representative_orig = (
                True if representative == representative_orig else False
            )
        except IndexError:
            representative_orig = False

        row = [
            representative,
            n_grids_per_cluster,
            relative_representation,
            represented_grids,
            representative_orig,
        ]
        df_data.append(row)

    cluster_df = pd.DataFrame(df_data, index=np.unique(labels), columns=columns)
    cluster_df.index.name = "cluster_id"

    return cluster_df.sort_values("n_grids_per_cluster", ascending=False)


def cluster_workflow(config=None):
    """
    Get cluster attributes per grid if needed and conduct MV grid clustering.

    Parameters
    ----------
    config : dict
        Config dict from config json. Can be obtained by calling
        ego.tools.utilities.get_scenario_setting(jsonpath=config_path).

    Returns
    --------
    pandas.DataFrame
        DataFrame with clustering results. Columns are "representative" containing
        the grid ID of the representative grid, "n_grids_per_cluster" containing the
        number of grids that are represented, "relative_representation" containing the
        percentage of grids represented, "represented_grids" containing a list of
        grid IDs of all represented grids and "representative_orig" containing
        information on whether the representative is the actual cluster center (in which
        case this value is True) or chosen because the grid in the cluster center is
        not a working grid.

    """
    # determine cluster attributes
    logger.info("Determine cluster attributes.")
    attributes_path = os.path.join(
        config["eGo"]["results_dir"], "mv_grid_cluster_attributes.csv"
    )
    if not os.path.exists(config["eGo"]["results_dir"]):
        os.makedirs(config["eGo"]["results_dir"])
    scenario = config["eTraGo"]["scn_name"]
    cluster_attributes_df = get_cluster_attributes(
        attributes_path=attributes_path, scenario=scenario, config=config
    )

    # select attributes to cluster by
    cluster_attributes_df = cluster_attributes_df[
        config["eDisGo"]["cluster_attributes"]
    ]
    working_grids_path = os.path.join(
        config["eGo"]["data_dir"], config["eDisGo"]["grid_path"], "working_grids.csv"
    )
    if os.path.isfile(working_grids_path):
        working_grids = pd.read_csv(working_grids_path, index_col=0)
    else:
        raise FileNotFoundError(
            "working_grids.csv is missing. Cannot conduct MV grid clustering."
        )
    # conduct MV grid clustering
    cluster_df = mv_grid_clustering(
        cluster_attributes_df, working_grids=working_grids, config=config
    )
    cluster_results_path = os.path.join(
        config["eGo"]["results_dir"], "mv_grid_cluster_results.csv"
    )
    cluster_df.to_csv(cluster_results_path)
    return cluster_df
