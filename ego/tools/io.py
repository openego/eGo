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
"""This file contains the eGo main class as well as input & output functions
of eGo in order to build the eGo application container.
"""

import logging
import os

import pandas as pd

if "READTHEDOCS" not in os.environ:
    import re

    from importlib import import_module

    import pypsa

    from egoio.tools import db
    from etrago import Etrago
    from etrago.appl import run_etrago
    from sqlalchemy.orm import sessionmaker

    from ego.tools.economics import etrago_convert_overnight_cost
    from ego.tools.edisgo_integration import EDisGoNetworks
    from ego.tools.plots import (
        igeoplot,
        plot_edisgo_cluster,
        plot_grid_storage_investment,
        plot_line_expansion,
        plot_storage_expansion,
        plot_storage_use,
        power_price_plot,
    )
    from ego.tools.utilities import get_scenario_setting

    from ego.mv_clustering import cluster_workflow

logger = logging.getLogger("ego")

__copyright__ = "Europa-Universität Flensburg, " "Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc"


class eGo:
    """Main eGo module which includs all results and main functionalities.


    Returns
    -------
    network_etrago: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    edisgo.network : :class:`ego.tools.edisgo_integration.EDisGoNetworks`
        Contains multiple eDisGo networks
    edisgo : :pandas:`pandas.Dataframe<dataframe>`
        aggregated results of eDisGo
    etrago : :pandas:`pandas.Dataframe<dataframe>`
        aggregated results of eTraGo


    """

    def __init__(self, jsonpath, *args, **kwargs):

        # Extract settings
        self.jsonpath = jsonpath
        self._json_file = get_scenario_setting(jsonpath=jsonpath)
        self.scn_name = self._json_file["eTraGo"]["scn_name"]

        # Database connection from json_file
        # self._connect_to_db()

    def run(self):
        """
        Run all grid optimization steps in the given scenario settings

        Returns
        -------
        None.

        """
        # Perform MV grid clustering
        self._mvlv_grid_choice_mode = self._json_file["eDisGo"]["choice_mode"]
        self.set_mvlv_grid_choice()

        # Run eTraGo for optimizing the eHV/HV grid
        self.etrago = self._setup_etrago()

        # Run eDisGo for optimizing MV/LV grids
        self.edisgo = self._setup_edisgo()

    def analyze_results(self):
        """
        Run all functions to analyze the results of the grid optimizations

        Returns
        -------
        None.

        """
        # Analyze results
        self._total_investment_costs = None
        self._total_operation_costs = None
        self._calculate_investment_cost()

    def _connect_to_db(self):
        try:
            conn = db.connection(section=self.json_file["eTraGo"]["db"])
            Session = sessionmaker(bind=conn)
            self.session = Session()
            logger.info("Connected to Database")
        except:  # noqa: E722
            logger.error("Failed connection to Database", exc_info=True)

    def _setup_etrago(self):
        """
        Run optimization of ehv/hv grid or load results from provious run
        """
        logger.info("eTraGo section started")
        cfg = self._json_file

        if cfg["eGo"].get("csv_import_eTraGo"):
            
            logger.info("Import eTraGo network from csv files")
            return Etrago(csv_folder_name=cfg["eGo"]["csv_import_eTraGo"])

        if cfg["eGo"]["eTraGo"] is True:

            from etrago.appl import args as default_args

            def deep_merge(base: dict, override: dict) -> dict:
                result = base.copy()
                for key, value in override.items():
                    if (
                        key in result
                        and isinstance(result[key], dict)
                        and isinstance(value, dict)
                    ):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result

            etrago_args = deep_merge(default_args, cfg["eTraGo"])
            # unify path to the path given in the superordinate eGo section
            etrago_args['csv_export'] = cfg["eGo"]["result_export_path"]+"/etrago_results"
            
            logger.info("Create eTraGo network calculated by eGo")
            return run_etrago(args=etrago_args, json_path=None)

        return None

    def _setup_edisgo(self):
        """
        Run optimization of selected mvlv grids

        Returns
        -------
        None.

        """
        if self._json_file["eGo"]["eDisGo"] is True:
            logger.info("Create eDisGo network")

            etrago_network = (
                self.etrago.disaggregated_network if self.etrago is not None else None
            )
            return EDisGoNetworks(
                json_file=self._json_file,
                mvlv_grid_choice=self.mvlv_grid_choice,
                etrago_network=etrago_network,
            )
        else:
            logger.info("No eDisGo network")
            return None

    def _calculate_investment_cost(self, storage_mv_integration=True):
        """Get total investment costs of all voltage level for storages
        and grid expansion
        """

        self._total_inv_cost = pd.DataFrame(
            columns=["component", "voltage_level", "capital_cost"]
        )
        _grid_ehv = None
        extendable = self.json_file["eTraGo"].get("extendable", {})
        extendable_list = (
            extendable
            if isinstance(extendable, list)
            else extendable.get("extendable_components", [])
        )
        if self.etrago is not None and "network" in extendable_list:
            _grid_ehv = self.etrago.grid_investment_costs
            _grid_ehv["component"] = "grid"

            self._total_inv_cost = pd.concat(
                [self._total_inv_cost, _grid_ehv], ignore_index=True
            )

        _storage = None
        if self.etrago is not None and "storage" in extendable_list:
            _storage = self.etrago.storage_investment_costs
            _storage["component"] = "storage"

            self._total_inv_cost = pd.concat(
                [self._total_inv_cost, _storage], ignore_index=True
            )

        _grid_mv_lv = None
        if self.json_file["eGo"]["eDisGo"] is True:

            _grid_mv_lv = self.edisgo.grid_investment_costs
            if _grid_mv_lv is not None:
                _grid_mv_lv["component"] = "grid"
                _grid_mv_lv["differentiation"] = "domestic"

                self._total_inv_cost = pd.concat(
                    [self._total_inv_cost, _grid_mv_lv], ignore_index=True
                )

        # add overnight costs
        self._total_investment_costs = self._total_inv_cost
        if (
            not self._total_inv_cost.empty
            and self.json_file["eTraGo"].get("end_snapshot") is not None
        ):
            self._total_investment_costs["overnight_costs"] = (
                etrago_convert_overnight_cost(
                    self._total_investment_costs["capital_cost"], self.json_file
                )
            )
        else:
            self._total_investment_costs["overnight_costs"] = None

        # Include MV storages into the _total_investment_costs dataframe
        if storage_mv_integration is True and self.etrago is not None:
            if _grid_mv_lv is not None:
                self._integrate_mv_storage_investment()

        # sort values
        self._total_investment_costs["voltage_level"] = pd.Categorical(
            self._total_investment_costs["voltage_level"],
            ["ehv", "hv", "mv", "lv", "mv/lv"],
        )
        self._total_investment_costs = self._total_investment_costs.sort_values(
            "voltage_level"
        )

        self._storage_costs = _storage
        self._ehv_grid_costs = _grid_ehv
        self._mv_grid_costs = _grid_mv_lv

    def _integrate_mv_storage_investment(self):
        """
        Updates the total investment costs dataframe and includes the
        storage integrated in MV grids.
        """

        costs_df = self._total_investment_costs

        total_stor = self._calculate_all_extended_storages()
        mv_stor = self._calculate_mv_storage()

        integrated_share = mv_stor / total_stor

        try:

            if integrated_share > 0:

                ehv_stor_idx = costs_df.index[
                    (costs_df["component"] == "storage")
                    & (costs_df["voltage_level"] == "ehv")
                ][0]

                int_capital_costs = (
                    costs_df.loc[ehv_stor_idx]["capital_cost"] * integrated_share
                )
                int_overnight_costs = (
                    costs_df.loc[ehv_stor_idx]["overnight_costs"] * integrated_share
                )

                costs_df.at[ehv_stor_idx, "capital_cost"] = (
                    costs_df.loc[ehv_stor_idx]["capital_cost"] - int_capital_costs
                )

                costs_df.at[ehv_stor_idx, "overnight_costs"] = (
                    costs_df.loc[ehv_stor_idx]["overnight_costs"] - int_overnight_costs
                )

                new_storage_row = {
                    "component": ["storage"],
                    "voltage_level": ["mv"],
                    "differentiation": ["domestic"],
                    "capital_cost": [int_capital_costs],
                    "overnight_costs": [int_overnight_costs],
                }

                new_storage_row = pd.DataFrame(new_storage_row)
                costs_df = pd.concat([costs_df, new_storage_row], ignore_index=True)

                self._total_investment_costs = costs_df
        except:  # noqa: E722
            logger.info("Something went wrong with the MV storage distribution.")

    def _calculate_all_extended_storages(self):
        """
        Returns the all extended storage p_nom_opt in MW.
        """
        etrago_network = self.etrago.disaggregated_network

        stor_df = etrago_network.storage_units.loc[
            etrago_network.storage_units["p_nom_extendable"]
        ]

        stor_df = stor_df[["bus", "p_nom_opt"]]

        all_extended_storages = stor_df["p_nom_opt"].sum()

        return all_extended_storages

    def _calculate_mv_storage(self):
        """
        Returns the storage p_nom_opt in MW, integrated in MV grids
        """
        etrago_network = self.etrago.disaggregated_network

        min_extended = 0.3
        stor_df = etrago_network.storage_units.loc[
            (etrago_network.storage_units["p_nom_extendable"])
            & (etrago_network.storage_units["p_nom_opt"] > min_extended)
            & (etrago_network.storage_units["max_hours"] <= 20.0)
        ]

        stor_df = stor_df[["bus", "p_nom_opt"]]

        integrated_storage = 0.0  # Storage integrated in MV grids

        for idx, row in stor_df.iterrows():
            mv_grid_id = row["bus"]
            p_nom_opt = row["p_nom_opt"]

            if not mv_grid_id:
                continue

            logger.info(
                "Checking storage integration for MV grid {}".format(mv_grid_id)
            )

            grid_choice = self.edisgo.grid_choice

            cluster = grid_choice.loc[
                [
                    mv_grid_id in repr_grids
                    for repr_grids in grid_choice["represented_grids"]
                ]
            ]

            if len(cluster) == 0:
                continue

            else:
                representative_grid = cluster["the_selected_network_id"].values[0]

            if hasattr(self.edisgo.network[representative_grid], "network"):
                integration_df = self.edisgo.network[
                    representative_grid
                ].network.results.storages

                integrated_power = integration_df["nominal_power"].sum() / 1000
            else:
                integrated_power = 0.0

            if integrated_power > p_nom_opt:
                integrated_power = p_nom_opt

            integrated_storage = integrated_storage + integrated_power

        return integrated_storage

    @property
    def total_investment_costs(self):
        """
        Contains all investment informations about eGo

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`

        """

        return self._total_investment_costs

    @property
    def total_operation_costs(self):
        """
        Contains all operation costs information about eGo

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`

        """
        self._total_operation_costs = self.etrago.operating_costs
        # append eDisGo

        return self._total_operation_costs

    def plot_total_investment_costs(self, filename=None, display=False, **kwargs):
        """Plot total investment costs"""

        if filename is None:
            filename = "results/plot_total_investment_costs.pdf"
            display = True

        return plot_grid_storage_investment(
            self._total_investment_costs, filename=filename, display=display, **kwargs
        )

    def plot_power_price(self, filename=None, display=False):
        """Plot power prices per carrier of calculation"""
        if filename is None:
            filename = "results/plot_power_price.pdf"
            display = True

        return power_price_plot(self, filename=filename, display=display)

    def plot_storage_usage(self, filename=None, display=False):
        """Plot storage usage by charge and discharge"""
        if filename is None:
            filename = "results/plot_storage_usage.pdf"
            display = True

        return plot_storage_use(self, filename=filename, display=display)

    def plot_edisgo_cluster(self, filename=None, display=False, **kwargs):
        """Plot the Clustering of selected Dingo networks"""
        if filename is None:
            filename = "results/plot_edisgo_cluster.pdf"
            display = True

        return plot_edisgo_cluster(self, filename=filename, display=display, **kwargs)

    def plot_line_expansion(self, **kwargs):
        """Plot line expantion per line"""

        return plot_line_expansion(self, **kwargs)

    def plot_storage_expansion(self, **kwargs):
        """Plot storage expantion per bus"""

        return plot_storage_expansion(self, **kwargs)

    @property
    def iplot(self):
        """Get iplot of results as html"""
        return igeoplot(self)

    def _cluster_mv_grids(self):
        """
        Clusters the MV grids based on the attributes, for a given number
        of MV grids

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`
            Dataframe containing the clustered MV grids and their weightings

        """
        cluster_df = cluster_workflow(config=self._json_file)
        # Filter for clusters with representatives.
        cluster_df = cluster_df[cluster_df["representative"].astype(bool)]
        return cluster_df

    def set_mvlv_grid_choice(self):
        """
        Sets the grid choice based on the settings file

        """

        choice_df = pd.DataFrame(
            columns=[
                "no_of_points_per_cluster",
                "the_selected_network_id",
                "represented_grids",
            ]
        )

        if self._mvlv_grid_choice_mode == "cluster":
            cluster_df = self._cluster_mv_grids()

            n_clusters = self._json_file["eDisGo"]["n_clusters"]
            n_clusters_found = cluster_df.shape[0]
            if n_clusters == n_clusters_found:
                logger.info(f"Clustering to {n_clusters} MV grids")
            else:
                logger.warning(
                    f"For {n_clusters} only for {n_clusters_found} clusters "
                    f"found working grids."
                )

            choice_df["the_selected_network_id"] = cluster_df["representative"]
            choice_df["no_of_points_per_cluster"] = cluster_df["n_grids_per_cluster"]
            choice_df["represented_grids"] = cluster_df["represented_grids"]

        elif self._mvlv_grid_choice_mode == "manual":
            man_grids = self._json_file["eDisGo"]["manual_grids"]

            choice_df["the_selected_network_id"] = man_grids
            choice_df["no_of_points_per_cluster"] = 1
            choice_df["represented_grids"] = [
                [mv_grid_id] for mv_grid_id in choice_df["the_selected_network_id"]
            ]

            logger.info("Calculating manually chosen MV grids {}".format(man_grids))

        elif self._mvlv_grid_choice_mode == "all":
            mv_grids = self._check_available_mv_grids()

            choice_df["the_selected_network_id"] = mv_grids
            choice_df["no_of_points_per_cluster"] = 1
            choice_df["represented_grids"] = [
                [mv_grid_id] for mv_grid_id in choice_df["the_selected_network_id"]
            ]

            no_grids = len(mv_grids)
            logger.info("Calculating all available {} MV grids".format(no_grids))

        choice_df = choice_df.sort_values("no_of_points_per_cluster", ascending=False)

        self.mvlv_grid_choice = choice_df
        
    @classmethod
    def import_results(cls, path):

        scenario_path = os.path.join(path, "config.json")
        ego = cls(jsonpath=scenario_path)
        cfg = ego._json_file
        cfg["eGo"]["result_export_path"] = path

        etrago_path = os.path.join(path, "etrago_results")
        if os.path.isdir(etrago_path):
            cfg["eGo"]["csv_import_eTraGo"] = etrago_path
            ego.etrago = ego._setup_etrago()
            logger.info("Imported eTraGo results from %s", etrago_path)
        else:
            ego.etrago = None
            logger.info("No eTraGo results found in %s", etrago_path)

        if os.path.isfile(os.path.join(path, "grid_choice.csv")):
            cfg["eGo"]["eDisGo"] = True            
            cfg["eGo"]["csv_import_eDisGo"] = path
            ego.mvlv_grid_choice = None
            ego.edisgo = ego._setup_edisgo()
            ego.mvlv_grid_choice = ego.edisgo.grid_choice
            logger.info("Imported eDisGo results from %s", path)
        else:
            ego.edisgo = None
            logger.info("No eDisGo results fround in %s", path)

        return ego
    
    # write_results_to_db():
    logging.info("Initialisation of eGo Results")


def results_to_excel(ego):
    """
    Wirte results of ego.total_investment_costs to an excel file
    """
    # Write the results as xlsx file
    # ToDo add time of calculation to file name
    # add xlsxwriter to setup
    writer = pd.ExcelWriter("open_ego_results.xlsx", engine="xlsxwriter")

    # write results of installed Capacity by fuels
    ego.total_investment_costs.to_excel(
        writer, index=False, sheet_name="Total Calculation"
    )

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    # buses


if __name__ == "__main__":
    pass
