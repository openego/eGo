# -*- coding: utf-8 -*-
# Copyright 2016-2026 Europa-Universität Flensburg,
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
This file is part of the eGo toolbox.
It contains the class definition for multiple eDisGo networks.
"""

__copyright__ = (
    "Flensburg University of Applied Sciences, "
    "Europa-Universität Flensburg, "
    "Centre for Sustainable Energy Systems"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "ClaraBuettner"

import copy
import multiprocessing as mp

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from edisgo import EDisGo
from edisgo.edisgo import import_edisgo_from_files
from edisgo.io.db import engine
from edisgo.network.results import Results
from sklearn.linear_model import LinearRegression

config = {
    "scenario": "StatusQuo",
    "grid_path": "/path/to_your/.dingo/grids",
    "conf_path": "egon-data.configuration.yaml",
    "grid_ids": [33128, 31942],
    "n_workers": 4,
    "save_grid_builds": False,
    "results_file": False,
}


def linear_regression(X, y):
    """Performs a linear regression

    Parameters
    ----------
    X : pd.Series
        Data on x-axis.
    y : pd.Series
        Data on y-axis.

    Returns
    -------
    slope : float64
        Resulting slope.
    intercept : float64
        Resulting intercept.

    """

    model = LinearRegression()
    model.fit(X, y)

    slope = model.coef_[0]
    intercept = model.intercept_

    return slope, intercept


def run_factor_load_mp(args):
    """Performs simulations for load case with a selected scaling factor for loads

    Parameters
    ----------
    args : list
        Parameters for analysis.

    Returns
    -------
    factor_load : float64
        Selected scaling factor for loads.
    p_slack : float64
        Maximum slack usage in load case simulation for selected load factor.
    costs: float64
        Grid expansion costs in load case simulation for selected load factor.

    """
    factor_load, edisgo, load_ts, mv_id = args

    try:
        print(f"Load factor {factor_load} for grid {mv_id}")

        edisgo_variance_load = copy.deepcopy(edisgo)

        edisgo_variance_load.timeseries.loads_active_power *= factor_load
        edisgo_variance_load.timeseries.loads_reactive_power *= factor_load
        edisgo_variance_load.timeseries.storage_units_active_power *= factor_load
        edisgo_variance_load.timeseries.storage_units_reactive_power *= factor_load

        edisgo_variance_load.reinforce(timesteps_pfa=load_ts, model="lv")

        p_slack = edisgo_variance_load.results.pfa_slack.p.max()
        costs = edisgo_variance_load.results.grid_expansion_costs["total_costs"].sum()

        return factor_load, p_slack, costs

    except Exception as e:
        print(f"Not solved for factor {factor_load}: {e}")
        return factor_load, None, None


def run_factor_generation_mp(args):
    """Performs simulations for feedin case with a selected scaling factor for generation

    Parameters
    ----------
    args : list
        Parameters for analysis.

    Returns
    -------
    factor_generation : float64
        Selected scaling factor for generation.
    p_slack : float64
        Maximum slack usage in feedin simulation for selected generation factor.
    costs: float64
        Grid expansion costs in feedin case simulation for selected generation factor.

    """
    factor_generation, edisgo, gen_ts, mv_id, noload = args

    try:
        print(f"Generation factor {factor_generation} for grid {mv_id}")

        edisgo_variance_gen = copy.deepcopy(edisgo)

        edisgo_variance_gen.timeseries.generators_active_power *= factor_generation
        edisgo_variance_gen.timeseries.generators_active_power *= factor_generation
        edisgo_variance_gen.timeseries.storage_units_active_power *= factor_generation
        edisgo_variance_gen.timeseries.storage_units_reactive_power *= factor_generation

        if noload:
            edisgo_variance_gen.timeseries.loads_active_power *= 0.0
            edisgo_variance_gen.timeseries.loads_reactive_power *= 0.0

        edisgo_variance_gen.reinforce(timesteps_pfa=gen_ts, model="lv")

        p_slack = edisgo_variance_gen.results.pfa_slack.p.max()
        costs = edisgo_variance_gen.results.grid_expansion_costs["total_costs"].sum()

        return factor_generation, p_slack, costs

    except Exception as e:
        print(f"Not solved for factor {factor_generation}: {e}")
        return factor_generation, None, None


def load_grid(mv_id, config):
    """Load distribution grid

    Parameters
    ----------
    mv_id : int
        Index of the selected distribution grid.
    config : dict
        Configuration list.

    Returns
    -------
    edisgo : edisgo object
        edisgo object containing the selected grid.

    """

    ding0_grid = Path(config["grid_path"]) / str(mv_id) / "topology"

    scenario = config["scenario"]

    edisgo = EDisGo(
        ding0_grid=ding0_grid,
        legacy_ding0_grids=False,
    )

    edisgo.set_time_series_worst_case_analysis()
    edisgo.reinforce()

    edisgo.results = Results(edisgo)

    # Load additional data for future scenario
    if scenario == "eGon2035":
        conf_path = config["conf_path"]
        db_engine = engine(path=conf_path)

        edisgo.results = Results(edisgo)
        timeindex = pd.date_range("2011-01-01 08:00", periods=12, freq="H")
        edisgo.set_timeindex(timeindex=timeindex)
        edisgo.import_generators(generator_scenario=scenario)
        edisgo.import_home_batteries(scenario=scenario, engine=db_engine)
        edisgo.import_heat_pumps(scenario=scenario, engine=db_engine)
        edisgo.import_dsm(scenario=scenario, engine=db_engine)
        edisgo.import_electromobility(
            data_source="oedb", scenario=scenario, engine=db_engine
        )

        edisgo.set_time_series_worst_case_analysis()
        edisgo.apply_charging_strategy()

    if config["save_grid_builds"]:
        edisgo.save(
            config["save_grid_builds"] + f"/{scenario}_mv_id_{mv_id}",
            save_topology=True,
            save_timeseries=True,
            save_results=True,
            save_electromobility=True,
            save_opf_results=True,
            save_heatpump=True,
            save_dsm=True,
            save_overlying_grid=True,
        )

    return edisgo


def run_mvlv_simulation(mv_id, config, add_feedin_noload=False):
    """Run bottom-up analysis for one selected mv grid

    Parameters
    ----------
    mv_id : int
        Index of the selected mv grid.
    config : dict
        Configuration list.
    add_feedin_noload : boolean, optional
        State if loads are set to zero in feedin case. The default is False.

    Returns
    -------
    df_results : pandas.DataFrame
        Resulting slack exchange and grid expansion costs for each load and feedin case.

    """

    scenario = config["scenario"]

    if config["save_grid_builds"]:
        try:
            edisgo = import_edisgo_from_files(
                config["save_grid_builds"] + f"/{scenario}_mv_id_{mv_id}",
                import_topology=True,
                import_timeseries=True,
                import_results=True,
                import_electromobility=True,
                import_opf_results=True,
                import_heat_pump=True,
                import_dsm=True,
                import_overlying_grid=True,
                from_zip_archive=False,
            )
            edisgo.results = Results(edisgo)
            edisgo.timeseries.reset()
            edisgo.set_time_series_worst_case_analysis()
        except:
            print(" -----------------------------------------------------------")
            print(f"MV Grid {mv_id} not available in the path. Building grid...")
            print(" -----------------------------------------------------------")
            edisgo = load_grid(mv_id, config)
    else:
        print(" -----------------------------------------------------------")
        print(f"Building MV Grid {mv_id}...")
        print(" -----------------------------------------------------------")
        edisgo = load_grid(mv_id, config)
        edisgo.set_time_series_worst_case_analysis()

    df_results = pd.DataFrame(columns=["p_slack", "costs"])

    # Define scaling factors used to change load and generation
    if scenario == "StatusQuo":
        factors_load = [
            1.0,
            1.1,
            1.2,
            1.3,
            1.5,
            1.75,
            2.0,
            2.5,
            3.0,
            4.0,
        ]
        factors_generation = [
            1.0,
            1.1,
            1.2,
            1.3,
            1.5,
            1.75,
            2.0,
            2.5,
            3.0,
            4.0,
        ]
    else:
        factors_load = [
            1.0,
            0.1,
            0.5,
            0.8,
            1.1,
            1.2,
            1.3,
            1.5,
            1.75,
            2.0,
            2.5,
            3.0,
            4.0,
        ]
        factors_generation = [
            1.0,
            0.1,
            0.5,
            0.8,
            1.1,
            1.2,
            1.3,
            1.5,
            1.75,
            2.0,
            2.5,
            3.0,
            4.0,
        ]

    # Store snapshots defining load and feed-in case
    load_ts = edisgo.timeseries.timeindex_worst_cases[
        edisgo.timeseries.timeindex_worst_cases.index.str.contains("load")
    ].values

    gen_ts = edisgo.timeseries.timeindex_worst_cases[
        edisgo.timeseries.timeindex_worst_cases.index.str.contains("feed")
    ].values

    args = [(factor_load, edisgo, load_ts, mv_id) for factor_load in factors_load]

    with mp.Pool(processes=config["n_workers"]) as pool:
        results = pool.map(run_factor_load_mp, args)

    for factor_load, p_slack, costs in results:
        if p_slack is not None:
            df_results.loc[f"Load{factor_load}", "p_slack"] = p_slack
            df_results.loc[f"Load{factor_load}", "costs"] = costs

    args = [
        (factor_generation, edisgo, gen_ts, mv_id, False)
        for factor_generation in factors_generation
    ]

    with mp.Pool(processes=config["n_workers"]) as pool:
        results = pool.map(run_factor_generation_mp, args)

    for factor_generation, p_slack, costs in results:
        if p_slack is not None:
            df_results.loc[f"Gen{factor_generation}", "p_slack"] = p_slack
            df_results.loc[f"Gen{factor_generation}", "costs"] = costs

    if add_feedin_noload:
        args = [
            (factor_generation, edisgo, gen_ts, mv_id, add_feedin_noload)
            for factor_generation in factors_generation
        ]

        with mp.Pool(processes=config["n_workers"]) as pool:
            results = pool.map(run_factor_generation_mp, args)

        for factor_generation, p_slack, costs in results:
            if p_slack is not None:
                df_results.loc[f"GenNoLoad{factor_generation}", "p_slack"] = p_slack
                df_results.loc[f"GenNoLoad{factor_generation}", "costs"] = costs

    return df_results


def plot_simulation_results(
    df_results,
    df,
    mv_id,
    color_l="red",
    marker_l="^",
    color_f="blue",
    marker_f="o",
    filename=None,
):
    """Create plot visualizing results of bottom-up analysis for one mv grid.

    Parameters
    ----------
    df_results : pandas.DataFrame
        Resulting slack exchange and grid expansion costs for each load and feedin case.
    df : pandas.DataFrame
        Results of linear regressions.
    mv_id : int
        Index of the selected mv grid.
    color_l : str, optional
        Color for load case results. The default is "red".
    marker_l : str, optional
        Marker for load case results. The default is "^".
    color_f : str, optional
        Color for feedin case results. The default is "blue".
    marker_f : str, optional
        Marker for feedin case results. The default is "o".
    filename : str, optional
        If plot should be saved, add path to file here. The default is None.

    Returns
    -------
    None.

    """
    df_load = df_results[df_results.index.str.startswith("Load")]
    df_feedin = df_results[df_results.index.str.startswith("Gen")]

    plt.scatter(df_load["p_slack"], df_load["costs"], c=color_l, marker=marker_l)
    plt.scatter(df_feedin["p_slack"], df_feedin["costs"], c=color_f, marker=marker_f)

    x_vals_l = np.linspace(df_load["p_slack"].min(), df_load["p_slack"].max(), 100)
    y_vals_l = df.loc[mv_id, "slope_load"] * x_vals_l + df.loc[mv_id, "intercept_load"]

    plt.plot(x_vals_l, y_vals_l, linestyle="--", color=color_l)

    x_vals_f = np.linspace(df_feedin["p_slack"].min(), df_feedin["p_slack"].max(), 100)
    y_vals_f = (
        df.loc[mv_id, "slope_feedin"] * x_vals_f + df.loc[mv_id, "intercept_feedin"]
    )

    plt.plot(x_vals_f, y_vals_f, linestyle="--", color=color_f)

    tick_size = 12
    plt.xticks(fontsize=tick_size)
    plt.yticks(fontsize=tick_size)

    plt.xlabel("slack exchange with HV grid [MW]", fontsize=tick_size)
    plt.ylabel("grid expansion costs [EUR]", fontsize=tick_size)

    patch_l = mpatches.Patch(color=color_l, label="Load Case")
    patch_f = mpatches.Patch(color=color_f, label="Feedin Case")

    plt.legend(handles=[patch_l, patch_f], fontsize=tick_size)

    plt.grid(True)

    if filename:
        plt.savefig(filename)
        plt.close()


def process_simulation_results(df_results, mv_id, config):
    """Use results of bottom-up simulations to derive exchange capacity with upper
    grid and its expansion costs.

    Parameters
    ----------
    df_results : pandas.DataFrame
        Resulting slack exchange and grid expansion costs for each load and feedin case.
    mv_id : int
        Index of the selected mv grid.
    config : dict
        Configuration list.

    Returns
    -------
    slope_load : float64
        Resulting slope from linear regression in load case.
    intercept_load : float64
        Resulting intercept from linear regression in load case.
    slope_feedin : float64
        Resulting slope from linear regression in feedin case.
    intercept_feedin : float64
        Resulting intercept from linear regression in feedin case.

    """

    if config["scenario"] == "StatusQuo":
        p_nom_load = df_results.p_slack["Load1.0"]
        p_nom_feedin = df_results.p_slack["Gen1.0"]
    else:
        p_nom_load = 0
        p_nom_feedin = 0

    df_load = df_results[
        (df_results.index.str.startswith("Load")) & (df_results.p_slack >= p_nom_load)
    ]
    df_feedin = df_results[
        (df_results.index.str.startswith("Gen")) & (df_results.p_slack <= p_nom_feedin)
    ]

    try:
        slope_load, intercept_load = linear_regression(
            df_load[["p_slack"]], df_load["costs"]
        )

    except ValueError as e:
        print(f"Regression for load case not possible for mv grid {mv_id}. {e}")
        slope_load, intercept_load = 0, 0

    try:
        slope_feedin, intercept_feedin = linear_regression(
            df_feedin[["p_slack"]], df_feedin["costs"]
        )

    except ValueError as e:
        print(f"Regression for load case not possible for mv grid {mv_id}. {e}")
        slope_feedin, intercept_feedin = 0, 0

    return slope_load, intercept_load, slope_feedin, intercept_feedin


def run_bottomup_analysis(config, all_results_path=None):
    """Run bottom-up analysis to derive exchange capacities between distribution grids
    and transmission grid and their expansion costs.

    Parameters
    ----------
    config : dict
        Settings stored in list.
    all_results_path : state, optional
        Path to folder where all results from the simulations are stored.
        The default is None.

    Returns
    -------
    df_interface : pandas.DataFrame
        Dataframe containing results that can be used for the interface to upper grids.

    """

    df = pd.DataFrame(
        columns=[
            "slope_load",
            "intercept_load",
            "slack_base_load",
            "slope_feedin",
            "intercept_feedin",
            "slack_base_feedin",
        ]
    )

    for mv_id in config["grid_ids"]:

        df_results = run_mvlv_simulation(mv_id, config)

        slope_load, intercept_load, slope_feedin, intercept_feedin = (
            process_simulation_results(df_results, mv_id, config)
        )

        df.loc[mv_id, "slope_load"] = slope_load
        df.loc[mv_id, "intercept_load"] = intercept_load
        df.loc[mv_id, "slope_feedin"] = slope_feedin
        df.loc[mv_id, "intercept_feedin"] = intercept_feedin

        df.loc[mv_id, "slack_base_load"] = df_results[
            (df_results.index.str.startswith("Load")) & (df_results.costs < 1)
        ].p_slack.max()

        df.loc[mv_id, "slack_base_feedin"] = df_results[
            (df_results.index.str.startswith("Gen")) & (df_results.costs < 1)
        ].p_slack.min()

        if all_results_path:
            df_results.to_csv(
                all_results_path + f"/bottom_up_simulation_results_mvid_{mv_id}.csv"
            )

    df_interface = pd.DataFrame(
        columns=[
            "p_nom_load",
            "p_nom_feedin",
            "p_nom_worst_case",
            "capital_cost_load",
            "capital_cost_feedin",
            "capital_cost_worst_case",
        ]
    )
    df_interface.loc[:, "p_nom_load"] = df.loc[:, "slack_base_load"].abs()
    df_interface.loc[:, "p_nom_feedin"] = df.loc[:, "slack_base_feedin"].abs()
    df_interface.loc[:, "capital_cost_load"] = df.loc[:, "slope_load"].abs()
    df_interface.loc[:, "capital_cost_feedin"] = df.loc[:, "slope_feedin"].abs()

    for i, row in df_interface.iterrows():
        # Use the smallest p_nom
        df_interface.loc[i, "p_nom_worst_case"] = df_interface.loc[i, "p_nom_load"]
        if df_interface.loc[i, "p_nom_worst_case"] > abs(
            df_interface.loc[i, "p_nom_feedin"]
        ):
            df_interface.loc[i, "p_nom_worst_case"] = abs(
                df_interface.loc[i, "p_nom_feedin"]
            )

        # Use the highest cost
        df_interface.loc[i, "capital_cost_worst_case"] = abs(
            df_interface.loc[i, "capital_cost_load"]
        )
        if df_interface.loc[i, "capital_cost_worst_case"] < abs(
            df_interface.loc[i, "capital_cost_feedin"]
        ):
            df_interface.loc[i, "capital_cost_worst_case"] = abs(
                df_interface.loc[i, "capital_cost_feedin"]
            )

    if config["results_file"]:
        df_interface.to_csv(config["results_file"])

    return df_interface
