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
This file is part of the eGo toolbox.
It contains the class definition for multiple eDisGo networks.
"""
__copyright__ = (
    "Flensburg University of Applied Sciences, "
    "Europa-Universität Flensburg, "
    "Centre for Sustainable Energy Systems"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc, mltja"

import json
import logging
import os
import pickle

from datetime import datetime
from datetime import timedelta as td
from time import localtime, sleep, strftime

# Import
from traceback import TracebackException

import dill
import multiprocess as mp2
import pandas as pd

if "READTHEDOCS" not in os.environ:
    from edisgo.edisgo import import_edisgo_from_files
    from edisgo.tools.plots import mv_grid_topology

    #from ego.mv_clustering import cluster_workflow, database
    from ego.tools.economics import edisgo_grid_investment
    from ego.tools.interface import ETraGoMinimalData, get_etrago_results_per_bus


# Logging
logger = logging.getLogger(__name__)

pickle.DEFAULT_PROTOCOL = 4
dill.settings["protocol"] = 4


class EDisGoNetworks:
    """
    Performs multiple eDisGo runs and stores the resulting edisgo_grids

    Parameters
    ----------
    json_file : :obj:dict
        Dictionary of the ``scenario_setting.json`` file
    etrago_network: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`

    """

    def __init__(self, json_file, mvlv_grid_choice, etrago_network=None):

        # Genral Json Inputs
        self._json_file = json_file
        self._set_scenario_settings()

        # Set grid choice from eGo
        self._grid_choice = mvlv_grid_choice

        # Create reduced eTraGo network (optional in eDisGo-only mode)
        if etrago_network is not None:
            self._etrago_network = ETraGoMinimalData(etrago_network, json_file)
        else:
            self._etrago_network = None
        del etrago_network

        # Program information
        self._run_finished = False

        # eDisGo Result grids
        self._edisgo_grids = {}

        if self._csv_import:
            self._load_edisgo_results()
            self._successful_grids = self._successful_grids()
            etrago_cfg = self._json_file.get("eTraGo", {})
            if (
                self._etrago_network is not None
                and etrago_cfg.get("end_snapshot") is not None
                and etrago_cfg.get("start_snapshot") is not None
            ):
                self._grid_investment_costs = edisgo_grid_investment(
                    self, self._json_file
                )
            else:
                logger.info(
                    "Skipping edisgo_grid_investment: no eTraGo snapshots."
                )
                self._grid_investment_costs = None

        else:
            # Execute Functions
            self._init_status()
            self._run_edisgo_pool()
            if self._results:
                self._save_edisgo_results()

            self._successful_grids = self._successful_grids()

            etrago_cfg = self._json_file.get("eTraGo", {})
            if (
                self._etrago_network is not None
                and etrago_cfg.get("end_snapshot") is not None
                and etrago_cfg.get("start_snapshot") is not None
            ):
                self._grid_investment_costs = edisgo_grid_investment(
                        self, self._json_file
                )
            else:
                logger.info(
                        "Skipping edisgo_grid_investment: no eTraGo snapshots "
                        "configured (annuity scaling requires eTraGo subset)."
                )
                self._grid_investment_costs = None

    @property
    def network(self):
        """
        Container for EDisGo objects, including all results

        Returns
        -------
        dict[int, :class:`edisgo.EDisGo`]
            Dictionary of EDisGo objects, keyed by MV grid ID

        """
        return self._edisgo_grids

    @property
    def grid_choice(self):
        """
        Container for the choice of MV grids, including their weighting

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`
            Dataframe containing the chosen grids and their weightings
            'no_of_points_per_cluster', 'the_selected_network_id', 'represented_grids'

        """
        return self._grid_choice

    @property
    def successful_grids(self):
        """
        Relative number of successfully calculated MV grids
        (Includes clustering weighting)

        Returns
        -------
        int
            Relative number of grids

        """
        return self._successful_grids

    @property
    def grid_investment_costs(self):
        """
        Grid investment costs

        Returns
        -------
        None or :pandas:`pandas.DataFrame<dataframe>`
            Dataframe containing annuity costs per voltage level

        """
        return self._grid_investment_costs

    def plot_storage_integration(self, mv_grid_id, **kwargs):
        """
        Plots storage position in MV grid of integrated storages.
        For more information see :func:`edisgo.tools.plots.mv_grid_topology`.
        """
        mv_grid_topology(
            self._edisgo_grids[mv_grid_id].network.pypsa,
            self._edisgo_grids[mv_grid_id].network.config,
            node_color=kwargs.get("storage_integration", None),
            filename=kwargs.get("filename", None),
            grid_district_geom=kwargs.get("grid_district_geom", True),
            background_map=kwargs.get("background_map", True),
            xlim=kwargs.get("xlim", None),
            ylim=kwargs.get("ylim", None),
            title=kwargs.get("title", ""),
        )

    def plot_grid_expansion_costs(self, mv_grid_id, **kwargs):
        """
        Plots costs per MV line.
        For more information see :func:`edisgo.tools.plots.mv_grid_topology`.
        """

        mv_grid_topology(
            self._edisgo_grids[mv_grid_id].network.pypsa,
            self._edisgo_grids[mv_grid_id].network.config,
            line_color="expansion_costs",
            grid_expansion_costs=(
                self._edisgo_grids[
                    mv_grid_id
                ].network.results.grid_expansion_costs.rename(
                    columns={"overnight_costs": "total_costs"}
                )
            ),
            filename=kwargs.get("filename", None),
            grid_district_geom=kwargs.get("grid_district_geom", True),
            background_map=kwargs.get("background_map", True),
            limits_cb_lines=kwargs.get("limits_cb_lines", None),
            xlim=kwargs.get("xlim", None),
            ylim=kwargs.get("ylim", None),
            lines_cmap=kwargs.get("lines_cmap", "inferno_r"),
            title=kwargs.get("title", ""),
        )

    def plot_line_loading(self, mv_grid_id, **kwargs):
        """
        Plots relative line loading (current from power flow analysis to
        allowed current) of MV lines.
        For more information see :func:`edisgo.tools.plots.mv_grid_topology`.
        """

        mv_grid_topology(
            self._edisgo_grids[mv_grid_id].network.pypsa,
            self._edisgo_grids[mv_grid_id].network.config,
            timestep=kwargs.get("timestep", None),
            line_color="loading",
            node_color=kwargs.get("node_color", None),
            line_load=self._edisgo_grids[mv_grid_id].network.results.s_res(),
            filename=kwargs.get("filename", None),
            arrows=kwargs.get("arrows", None),
            grid_district_geom=kwargs.get("grid_district_geom", True),
            background_map=kwargs.get("background_map", True),
            voltage=None,  # change API
            limits_cb_lines=kwargs.get("limits_cb_lines", None),
            limits_cb_nodes=kwargs.get("limits_cb_nodes", None),
            xlim=kwargs.get("xlim", None),
            ylim=kwargs.get("ylim", None),
            lines_cmap=kwargs.get("lines_cmap", "inferno_r"),
            title=kwargs.get("title", ""),
        )

    def plot_mv_grid_topology(self, mv_grid_id, **kwargs):
        """
        Plots plain MV grid topology.
        For more information see :func:`edisgo.tools.plots.mv_grid_topology`.
        """

        mv_grid_topology(
            self._edisgo_grids[mv_grid_id].network.pypsa,
            self._edisgo_grids[mv_grid_id].network.config,
            filename=kwargs.get("filename", None),
            grid_district_geom=kwargs.get("grid_district_geom", True),
            background_map=kwargs.get("background_map", True),
            xlim=kwargs.get("xlim", None),
            ylim=kwargs.get("ylim", None),
            title=kwargs.get("title", ""),
        )

    def _init_status(self):
        """
        Creates a status csv file where statuses of MV grid calculations are tracked.

        The file is saved to the directory 'status'. Filename indicates date and time
        the file was created.

        File contains the following information:

        * 'MV grid id' (index)
        * 'cluster_perc' - percentage of grids represented by this grid
        * 'start_time' - start time of calculation
        * 'end_time' - end time of calculation

        """
        self._status_dir = os.path.join(self._json_file["eGo"]["result_export_path"], "status")
        if not os.path.exists(self._status_dir):
            os.makedirs(self._status_dir)

        self._status_file_name = "eGo_" + strftime("%Y-%m-%d_%H%M%S", localtime())

        status = self._grid_choice.copy()
        status = status.set_index("the_selected_network_id")
        status.index.names = ["MV grid id"]

        status["cluster_perc"] = (
            status["no_of_points_per_cluster"]
            / self._grid_choice["no_of_points_per_cluster"].sum()
        )

        status["start_time"] = "Not started yet"
        status["end_time"] = "Not finished yet"

        status.drop(
            ["no_of_points_per_cluster", "represented_grids"], axis=1, inplace=True
        )

        self._status_file_path = os.path.join(
            self._status_dir, self._status_file_name + ".csv"
        )

        status.to_csv(self._status_file_path)

    def _status_update(self, mv_grid_id, time, message=None, show=True):
        """
        Updates status csv file where statuses of MV grid calculations are tracked.

        Parameters
        ----------
        mv_grid_id : int
            MV grid ID of the ding0 grid.
        time : str
            Can be either 'start' to set information on when the calculation started
            or 'end' to set information on when the calculation ended. In case a
            message is provided through parameter `message`, the message instead of the
            time is set.
        message : str or None (optional)
            Message to set for 'start_time' or 'end_time'. If None, the current time
            is set. Default: None.
        show : bool (optional)
            If True, shows a logging message with the status information. Default: True.

        """
        status = pd.read_csv(self._status_file_path, index_col=0)

        status["start_time"] = status["start_time"].astype(str)
        status["end_time"] = status["end_time"].astype(str)

        if message:
            now = message
        else:
            now = strftime("%Y-%m-%d_%H:%M", localtime())

        if time == "start":
            status.at[mv_grid_id, "start_time"] = now
        elif time == "end":
            status.at[mv_grid_id, "end_time"] = now
        if show:
            logger.info("\n\neDisGo status: \n\n" + status.to_string() + "\n\n")

        status.to_csv(self._status_file_path)

    def _update_edisgo_configs(self, edisgo_grid):
        """
        This function overwrites some eDisGo configurations with eGo
        settings.

        The overwritten configs are:

        * config['db_connection']['section']
        * config['data_source']['oedb_data_source']
        * config['versioned']['version']

        """
        # Info and Warning handling
        if not hasattr(self, "_suppress_log"):
            self._suppress_log = False  # Only in the first run warnings and
            # info get thrown

        # Versioned
        ego_gridversion = self._grid_version
        if ego_gridversion is None:
            ego_versioned = "model_draft"
            if not self._suppress_log:
                logger.info(
                    "eGo's grid_version == None is "
                    + "evaluated as data source: model_draft"
                )
        else:
            ego_versioned = "versioned"
            if not self._suppress_log:
                logger.info(
                    (
                        "eGo's grid_version == '{}' is "
                        + "evaluated as data source: versioned"
                    ).format(ego_gridversion)
                )

        edisgo_versioned = edisgo_grid.network.config["data_source"]["oedb_data_source"]

        if not ego_versioned == edisgo_versioned:
            if not self._suppress_log:
                logger.warning(
                    (
                        "eDisGo data source configuration ('{}') "
                        + "will be overwritten with data source config. from "
                        + "eGo's scenario settings (data source: '{}')"
                    ).format(edisgo_versioned, ego_versioned)
                )
            edisgo_grid.network.config["data_source"][
                "oedb_data_source"
            ] = ego_versioned

        # Gridversion
        ego_gridversion = self._grid_version
        edisgo_gridversion = edisgo_grid.network.config["versioned"]["version"]

        if not ego_gridversion == edisgo_gridversion:
            if not self._suppress_log:
                logger.warning(
                    (
                        "eDisGo version configuration (version: '{}') "
                        + "will be overwritten with version configuration "
                        + "from eGo's scenario settings (version: '{}')"
                    ).format(edisgo_gridversion, ego_gridversion)
                )
            edisgo_grid.network.config["versioned"]["version"] = ego_gridversion

        self._suppress_log = True

    def _set_scenario_settings(self):

        self._csv_import = self._json_file["eGo"]["csv_import_eDisGo"]

        # eTraGo args (may be absent/minimal in eDisGo-only mode)
        self._etrago_args = self._json_file.get("eTraGo", {})
        self._scn_name = self._etrago_args.get("scn_name", "eGon2035")
        extendable = self._etrago_args.get("extendable", {})
        extendable_list = (
            extendable if isinstance(extendable, list)
            else extendable.get("extendable_components", [])
        )
        self._ext_storage = "storage" in extendable_list
        if self._ext_storage:
            logger.info("eTraGo Dataset used extendable storage")

        self._pf_post_lopf = self._etrago_args.get("pf_post_lopf", False)

        # eDisGo args import
        if self._csv_import:
            #            raise NotImplementedError

            with open(os.path.join(self._csv_import, "edisgo_args.json")) as f:
                edisgo_args = json.load(f)

            self._json_file["eDisGo"] = edisgo_args
            logger.info(
                "All eDisGo settings are taken from CSV folder"
                + "(scenario settings are ignored)"
            )
            # This overwrites the original object...

        # Imported or directly from the Settings
        # eDisGo section of the settings
        self._edisgo_args = self._json_file["eDisGo"]

        # Reading all eDisGo settings
        # TODO: Integrate into a for-loop
        self._grid_version = self._edisgo_args["gridversion"]
        self._solver = self._edisgo_args["solver"]
        self._grid_path = self._edisgo_args["grid_path"]
        self._choice_mode = self._edisgo_args["choice_mode"]
        self._parallelization = self._edisgo_args["parallelization"]
        self._cluster_attributes = self._edisgo_args["cluster_attributes"]
        self._max_workers = self._edisgo_args["max_workers"]
        self._max_cos_phi_renewable = self._edisgo_args["max_cos_phi_renewable"]
        self._results = self._json_file["eGo"]["result_export_path"]
        self._max_calc_time = self._edisgo_args["max_calc_time"]
        # Optional: name of an edisgo.run preset. When set, run_edisgo()
        # delegates the per-grid workflow to edisgo.run.run_edisgo().
        self._preset = self._edisgo_args.get("preset")

        # Versioning
        if self._grid_version is not None:
            self._versioned = True
        else:
            self._versioned = False

    def _successful_grids(self):
        """
        Calculates the relative number of successfully calculated grids,
        including the cluster weightings
        """

        total, success, fail = 0, 0, 0
        for key, value in self._edisgo_grids.items():

            weight = self._grid_choice.loc[
                self._grid_choice["the_selected_network_id"] == key
            ]["no_of_points_per_cluster"].values[0]

            total += weight
            if hasattr(value, "network"):
                success += weight
            else:
                fail += weight
        return success / total

    def _identify_extended_storages(self):

        all_mv_grids = self._check_available_mv_grids()

        storages = pd.DataFrame(index=all_mv_grids, columns=["storage_p_nom"])

        logger.info("Identifying extended storage")
        for mv_grid in all_mv_grids:

            min_extended = 0.3
            stor_p_nom = self._etrago_network.storage_units.loc[
                (self._etrago_network.storage_units["bus"] == str(mv_grid))
                & (
                    self._etrago_network.storage_units["p_nom_extendable"]
                    == True  # noqa: E712
                )
                & (self._etrago_network.storage_units["p_nom_opt"] > min_extended)
                & (self._etrago_network.storage_units["max_hours"] <= 20.0)
            ]["p_nom_opt"]

            if len(stor_p_nom) == 1:
                stor_p_nom = stor_p_nom.values[0]
            elif len(stor_p_nom) == 0:
                stor_p_nom = 0.0
            else:
                raise IndexError

            storages.at[mv_grid, "storage_p_nom"] = stor_p_nom

        return storages

    def _check_available_mv_grids(self):
        """
        Checks all available MV grids in the given folder (from the settings)

        Returns
        -------
        :obj:`list`
            List of MV grid ID's

        """
        mv_grids = []
        for file in os.listdir(self._grid_path):
            if os.path.isdir(os.path.join(self._grid_path, file)):
                mv_grids.append(int(file))
        return mv_grids

    def _run_edisgo_pool(self):
        """
        Runs eDisGo for the chosen grids

        """
        parallelization = self._parallelization

        results_dir = self._results
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        if parallelization is True:
            logger.info("Run eDisGo parallel")
            mv_grids = self._grid_choice["the_selected_network_id"].tolist()
            no_cpu = mp2.cpu_count()
            if no_cpu > self._max_workers:
                no_cpu = self._max_workers
                logger.info(
                    "Number of workers limited to {} by user".format(self._max_workers)
                )

            self._edisgo_grids = set(mv_grids)
            self._edisgo_grids = parallelizer(
                mv_grids,
                lambda *xs: xs[1].run_edisgo(xs[0]),
                (self,),
                self._max_calc_time,
                workers=no_cpu,
            )

            for g in mv_grids:
                if g not in self._edisgo_grids:
                    self._edisgo_grids[g] = "Timeout"

        else:
            logger.info("Run eDisGo sequencial")
            no_grids = len(self._grid_choice)
            count = 0
            for idx, row in self._grid_choice.iterrows():
                prog = "%.1f" % (count / no_grids * 100)
                logger.info("{} % Calculated by eDisGo".format(prog))

                mv_grid_id = int(row["the_selected_network_id"])
                logger.info("MV grid {}".format(mv_grid_id))
                try:
                    edisgo_grid = self.run_edisgo(mv_grid_id)
                    self._edisgo_grids[mv_grid_id] = edisgo_grid
                except Exception as e:
                    self._edisgo_grids[mv_grid_id] = e
                    logger.exception("MV grid {} failed: \n".format(mv_grid_id))
                count += 1

        self._csv_import = self._json_file["eGo"]["result_export_path"]
        self._save_edisgo_results()
        self._load_edisgo_results()
        self._run_finished = True

    def _build_run_edisgo_config(self, mv_grid_id):
        """
        Build a config dict for ``edisgo.run.run_edisgo`` for one grid.

        Returns a dict that uses ``extends: <preset>`` so the runner
        resolves the bundled preset and merges grid-specific overrides
        on top.
        """
        cfg = {
            "extends": self._preset,
            "scenario": self._scn_name,
            "grid": {
                "ding0_path": os.path.join(self._grid_path, str(mv_grid_id)),
            },
            "results": {
                "directory": os.path.join(self._results, str(mv_grid_id)),
            },
        }
        db_block = self._json_file.get("database")
        ssh_block = self._json_file.get("ssh")
        if db_block is not None or ssh_block is not None:
            cfg["database"] = {}
            if db_block is not None:
                cfg["database"].update(db_block)
            if ssh_block is not None:
                cfg["database"]["ssh"] = ssh_block
        source = self._json_file.get("eDisGo", {}).get("overlying_grid_source")
        overlying_grid = self._json_file.get("eDisGo", {}).get("overlying_grid")
        if overlying_grid:
            if source == "etrago":
                cfg["overlying_grid"] = {"enabled": True, "source": "etrago"}
            elif source:
                cfg["overlying_grid"] = {
                    "enabled": True,
                    "source": "csv",
                    "path": os.path.join(source, str(mv_grid_id)),
                }
            else:
                cfg["overlying_grid"] = {"enabled": False}
        else:
            cfg["overlying_grid"] = {"enabled": False}

        # Timestep selection (uc5): a default block applied to every grid, with
        # optional per-grid overrides keyed by MV grid id. Injected as the
        # top-level ``timeseries_selection`` block the eDisGo select_timesteps
        # task reads from ``ctx.raw_config`` — mirroring the overlying_grid
        # injection above.
        edisgo_cfg = self._json_file.get("eDisGo", {})
        ts_default = edisgo_cfg.get("timeseries_selection")
        ts_per_grid = edisgo_cfg.get("timeseries_selection_per_grid", {}) or {}
        ts_selection = ts_per_grid.get(str(mv_grid_id), ts_default)
        if ts_selection is not None:
            cfg["timeseries_selection"] = ts_selection

        # Spatial complexity reduction (uc6): same default + per-grid-override
        # pattern as timeseries_selection above. Injected as the top-level
        # ``spatial_reduction`` block the eDisGo spatial_reduce/spatial_restore
        # tasks read from ``ctx.raw_config``.
        spatial_default = edisgo_cfg.get("spatial_reduction")
        spatial_per_grid = edisgo_cfg.get("spatial_reduction_per_grid", {}) or {}
        spatial_reduction = spatial_per_grid.get(str(mv_grid_id), spatial_default)
        if spatial_reduction is not None:
            cfg["spatial_reduction"] = spatial_reduction
        return cfg

    def _run_one_grid_via_runner(self, mv_grid_id):
        """
        Delegate the per-grid eDisGo workflow to edisgo.run.run_edisgo.
        """
        from edisgo.run import run_edisgo as edisgo_runner

        self._status_update(mv_grid_id, "start", show=False)
        results_dir = os.path.join(self._results, str(mv_grid_id))
        os.makedirs(results_dir, exist_ok=True)
        overlying_grid_data = None
        if self._json_file.get("eGo", {}).get("eTraGo"):
            if (self._json_file.get("eDisGo", {}).get("overlying_grid_source") == "etrago"  
            and self._json_file.get("eDisGo", {}).get("overlying_grid")):
                # if instead of "etrago" a file path is passed as source for the overlying grid data, 
                # tha data is loaded inside of edisgo from the provided directory
                overlying_grid_data = get_etrago_results_per_bus(
                    str(mv_grid_id),
                    self._etrago_network,
                    self._pf_post_lopf["active"],
                    self._max_cos_phi_renewable,
                )

                os.makedirs(self._results+"/overlying_grid", exist_ok=True)
                self._export_overlying_grid_data(
                    overlying_grid_data,
                    mv_grid_id,
                    path=self._results+"/overlying_grid/"
                    )
        cfg = self._build_run_edisgo_config(mv_grid_id)
        logger.info(
            "MV grid %s: delegating to edisgo.run.run_edisgo (preset=%s)",
            mv_grid_id, self._preset,
        )


        edisgo_grid = edisgo_runner(cfg,overlying_grid_data=overlying_grid_data)
        self._status_update(mv_grid_id, "end")
        return edisgo_grid


    def _export_overlying_grid_data(self, overlying_grid_data, mv_grid_id, path):

        output_dir = path + f"{str(mv_grid_id)}/"
        os.makedirs(output_dir, exist_ok=True)

        for key, series in overlying_grid_data.items():
            if (key != "timeindex") & (type(series) in [pd.Series, pd.DataFrame]):
                filepath = os.path.join(output_dir, f"{key}.csv")
                series.to_csv(filepath, index=True, header=True)


    def run_edisgo(self, mv_grid_id):
        """
        Performs a single eDisGo run.

        Delegates to :meth:`_run_one_grid_via_runner` when a preset is
        configured; otherwise raises NotImplementedError.
        """
        if self._preset:
            return self._run_one_grid_via_runner(mv_grid_id)
        raise NotImplementedError(
            "Legacy run_edisgo path removed. Set 'preset' in eDisGo config."
        )

    def _save_edisgo_results(self):
        results_dir = self._results
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        with open(os.path.join(results_dir, "edisgo_args.json"), "w") as fp:
            json.dump(self._edisgo_args, fp)

        self._grid_choice.to_csv(os.path.join(results_dir, "grid_choice.csv"))

    def _load_edisgo_results(self):
        """
        Loads eDisGo data for all specified grids

        Returns
        --------
        dict[]

        """

        # Load the grid choice from CSV
        results_dir = self._results
        self._grid_choice = pd.read_csv(
            os.path.join(results_dir, "grid_choice.csv"), index_col=0
        )
        self._grid_choice["represented_grids"] = self._grid_choice.apply(
            lambda x: eval(x["represented_grids"]), axis=1
        )

        for idx, row in self._grid_choice.iterrows():
            mv_grid_id = int(row["the_selected_network_id"])

            zip_path = os.path.join(
                self._csv_import, str(mv_grid_id), "main.zip"
            )
            try:
                edisgo_grid = import_edisgo_from_files(
                    edisgo_path=zip_path,
                    import_topology=True,
                    import_timeseries=False,
                    import_results=True,
                    import_electromobility=False,
                    from_zip_archive=True,
                    dtype="float32",
                    parameters={
                        "powerflow_results": ["pfa_p", "pfa_q"],
                        "grid_expansion_results": ["grid_expansion_costs"],
                    },
                )

                self._edisgo_grids[mv_grid_id] = edisgo_grid

                logger.info("Imported MV grid {}".format(mv_grid_id))
            except:  # noqa: E722
                self._edisgo_grids[mv_grid_id] = "This grid failed to reimport"

                logger.warning("MV grid {} could not be loaded".format(mv_grid_id))


class _ETraGoData:
    """
    Container for minimal eTraGo network.

    This minimal network only contains information relevant for eDisGo.

    Parameters
    ----------
    etrago_network : :pypsa:`PyPSA.Network<network>`

    """

    def __init__(self, etrago_network):
        def filter_by_carrier(
            etrago_network_obj, component, carrier, like=True, timeseries=True
        ):
            def filter_df_by_carrier(df):
                if isinstance(carrier, str):
                    if like:
                        return df[df.carrier.str.contains(carrier)]
                    else:
                        return df[df.carrier == carrier]
                elif isinstance(carrier, list):
                    return df[df.carrier.isin(carrier)]
                elif carrier is None:
                    return df

            if timeseries:
                attribute_to_save = {
                    "links": "p0",
                    "generators": "p",
                    "stores": "p",
                    "storage_units": "p",
                }
                attribute_to_save = attribute_to_save[component]

                df_to_filter = getattr(
                    getattr(etrago_network_obj, component + "_t"), attribute_to_save
                )
                df = df_to_filter.loc[
                    :,
                    filter_df_by_carrier(getattr(etrago_network_obj, component)).index,
                ]
            else:
                columns_to_save = {
                    "links": ["carrier", "p_nom"],
                    "generators": ["carrier", "p_nom"],
                    "stores": ["carrier", "e_nom"],
                    "storage_units": ["carrier", "p_nom", "max_hours"],
                }
                columns_to_save = columns_to_save[component]

                df_to_filter = getattr(etrago_network_obj, component)
                df = filter_df_by_carrier(df_to_filter)
                df = df[columns_to_save]

            unique_carriers = filter_df_by_carrier(
                getattr(etrago_network_obj, component)
            ).carrier.unique()
            logger.debug(
                f"{component}, {carrier}, {timeseries}, {df.shape}, {unique_carriers}"
            )

            return df

        logger.debug(
            f"Carriers in links " f"{etrago_network.network.links.carrier.unique()}"
        )
        logger.debug(
            f"Carriers in generators "
            f"{etrago_network.network.generators.carrier.unique()}"
        )
        logger.debug(
            f"Carriers in stores " f"{etrago_network.network.stores.carrier.unique()}"
        )
        logger.debug(
            f"Carriers in storage_units "
            f"{etrago_network.network.storage_units.carrier.unique()}"
        )

        self.snapshots = etrago_network.network.snapshots

        self.bev_charger = filter_by_carrier(
            etrago_network.network, "links", "BEV", timeseries=False
        )
        self.bev_charger_t = filter_by_carrier(
            etrago_network.network, "links", "BEV", timeseries=True
        )
        self.dsm = filter_by_carrier(
            etrago_network.network, "links", "dsm", timeseries=False
        )
        self.dsm_t = filter_by_carrier(
            etrago_network.network, "links", "dsm", timeseries=True
        )

        self.rural_heat_t = filter_by_carrier(
            etrago_network.network, "links", "rural_heat_pump", timeseries=True
        )
        self.rural_heat_store = filter_by_carrier(
            etrago_network.network, "stores", "rural_heat_store", timeseries=False
        )

        self.central_heat_t = filter_by_carrier(
            etrago_network.network,
            "links",
            ["central_heat_pump", "central_resistive_heater"],
            timeseries=True,
        )
        self.central_heat_store = filter_by_carrier(
            etrago_network.network, "stores", "central_heat_store", timeseries=False
        )

        self.central_gas_chp_t = filter_by_carrier(
            etrago_network.network, "links", "central_gas_chp_t", timeseries=True
        )

        #
        self.generators = filter_by_carrier(
            etrago_network.network, "generators", None, timeseries=False
        )
        self.generators_t = filter_by_carrier(
            etrago_network.network, "generators", None, timeseries=True
        )

        self.battery_storage_units = filter_by_carrier(
            etrago_network.network, "storage_units", "battery", timeseries=False
        )
        self.battery_storage_units_t = filter_by_carrier(
            etrago_network.network, "storage_units", "battery", timeseries=True
        )


def parallelizer(
    ding0_id_list,
    func,
    func_arguments,
    max_calc_time,
    workers=mp2.cpu_count(),
    worker_lifetime=1,
):
    """
    Use python multiprocessing toolbox for parallelization

    Several grids are analyzed in parallel based on your custom function that
    defines the specific application of eDisGo.

    Parameters
    ----------
    ding0_id_list : list of int
        List of ding0 grid data IDs (also known as HV/MV substation IDs)
    func : any function
        Your custom function that shall be parallelized
    func_arguments : tuple
        Arguments to custom function ``func``
    workers: int
        Number of parallel process
    worker_lifetime : int
        Bunch of grids sequentially analyzed by a worker

    Notes
    -----
    Please note, the following requirements for the custom function which is to
    be executed in parallel

    #. It must return an instance of the type :class:`~.edisgo.EDisGo`.
    #. The first positional argument is the MV grid district id (as int). It is
       prepended to the tuple of arguments ``func_arguments``


    Returns
    -------
    containers : dict of :class:`~.edisgo.EDisGo`
        Dict of EDisGo instances keyed by its ID
    """

    def collect_pool_results(result):
        """
        Store results from parallelized calculation in structured manner

        Parameters
        ----------
        result: :class:`~.edisgo.EDisGo`
        """
        results.update(result)

    def error_callback(key):

        #        message='Failed'
        #        func_arguments[0]._status_update(key, 'end', message)
        return lambda o: results.update({key: o})

    results = {}
    max_calc_time_seconds = max_calc_time * 3600

    def initializer():
        import pickle

        pickle.DEFAULT_PROTOCOL = 4
        import dill

        dill.settings["protocol"] = 4

    pool = mp2.Pool(workers, initializer=initializer, maxtasksperchild=worker_lifetime)

    result_objects = {}
    for ding0_id in ding0_id_list:
        edisgo_args = (ding0_id, *func_arguments)

        result_objects[ding0_id] = pool.apply_async(
            func=func,
            args=edisgo_args,
            callback=collect_pool_results,
            error_callback=error_callback(ding0_id),
        )

    errors = {}
    successes = {}
    start = datetime.now()
    end = (start + td(hours=max_calc_time)).isoformat(" ")
    logger.info("Jobs started. They will time out at {}.".format(end[: end.index(".")]))
    current = datetime.now()
    time_spent = 0
    while result_objects and ((current - start).seconds <= max_calc_time_seconds):
        done = []
        tick = (current - start).seconds * 100 / max_calc_time_seconds
        if tick - time_spent >= 1 or tick > 100:
            hours_to_go = (current - start).seconds / 3600
            logger.info(
                "{:.2f}% ({:.2f}/{}h) spent".format(tick, hours_to_go, max_calc_time)
            )
            logger.info("Jobs time out in {:.2f}h.".format(max_calc_time - hours_to_go))
            time_spent = tick
        for grid_id, result in result_objects.items():
            if result.ready():
                logger.info(
                    "MV grid {} ready. Trying to `get` the result.".format(grid_id)
                )
                done.append(grid_id)
                if not result.successful():
                    try:
                        # We already know that this was not successful, so the
                        # `get` is only here to re-raise the exception that
                        # occurred.
                        result.get()
                    except Exception as e:
                        logger.warning(
                            "MV grid {} failed due to {e!r}: '{e}'.".format(
                                grid_id, e=e
                            )
                        )
                        errors[grid_id] = e
                else:
                    logger.info("MV grid {} calculated successfully.".format(grid_id))
                    successes[grid_id] = result.get()
                logger.info("Done `get`ting the result for MV grid {}.".format(grid_id))
        for grid_id in done:
            del result_objects[grid_id]
        sleep(1)
        current = datetime.now()

    # Now we know that we either reached the timeout, (x)or that all
    # calculations are done. We just have collect what exactly is the case.
    # This is done by `get`ting the results with a timeout of 0. If any of them
    # are not yet done, a `TimeoutError` will be triggered, which we can
    # collect like all other errors.
    if not result_objects:
        logger.info("All MV grids stopped before the timeout.")
    else:
        logger.warning("Some MV grid simulations timed out.")
        pool.terminate()

    end = datetime.now()
    delta = end - start
    logger.info("Execution finished after {:.2f} hours".format(delta.seconds / 3600))

    done = []
    for grid_id, result in result_objects.items():
        done.append(grid_id)
        try:
            successes[grid_id] = result.get(timeout=0)
            logger.info("MV grid {} calculated successfully.".format(grid_id))
        except Exception as e:
            logger.warning(
                "MV grid {} failed due to {e!r}: '{e}'.".format(grid_id, e=e)
            )
            errors[grid_id] = e
    for grid_id in done:
        del result_objects[grid_id]

    if errors:
        logger.info("MV grid calculation error details:")
        for grid_id, error in errors.items():
            logger.info("  {}".format(grid_id))
            strings = TracebackException.from_exception(error).format()
            lines = [line for string in strings for line in string.split("\n")]
            for line in lines:
                logger.info("    " + line)

    pool.close()
    pool.join()

    return results
