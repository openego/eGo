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
This file is part of the the eGo toolbox.
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

from sqlalchemy.orm import scoped_session, sessionmaker

if "READTHEDOCS" not in os.environ:

    from edisgo.edisgo import import_edisgo_from_files
    from edisgo.tools.logger import setup_logger
    from edisgo.tools.plots import mv_grid_topology
    from egoio.db_tables import grid, model_draft
    from egoio.tools import db

    from ego.mv_clustering import cluster_workflow
    from ego.mv_clustering.database import get_engine, register_tables_in_saio
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

    def __init__(self, json_file, etrago_network):

        # Genral Json Inputs
        self._json_file = json_file
        self._set_scenario_settings()

        # Create reduced eTraGo network
        self._etrago_network = ETraGoMinimalData(etrago_network)
        del etrago_network

        # Program information
        self._run_finished = False

        # eDisGo Result grids
        self._edisgo_grids = {}

        if self._csv_import:
            self._load_edisgo_results()
            self._successful_grids = self._successful_grids()
            self._grid_investment_costs = edisgo_grid_investment(self, self._json_file)

        else:
            # Only clustering results
            if self._only_cluster:
                self._set_grid_choice()
                if self._results:
                    self._save_edisgo_results()
                self._grid_investment_costs = None

            else:
                # Execute Functions
                self._set_grid_choice()
                self._init_status()
                self._run_edisgo_pool()
                if self._results:
                    self._save_edisgo_results()

                self._successful_grids = self._successful_grids()

                self._grid_investment_costs = edisgo_grid_investment(
                    self, self._json_file
                )

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

    def get_mv_grid_from_bus_id(self, bus_id):
        """
        Queries the MV grid ID for a given eTraGo bus

        Parameters
        ----------
        bus_id : int
            eTraGo bus ID

        Returns
        -------
        int
            MV grid (ding0) ID

        """

        conn = db.connection(section=self._db_section)
        session_factory = sessionmaker(bind=conn)
        Session = scoped_session(session_factory)
        session = Session()

        mv_grid_id = self._get_mv_grid_from_bus_id(session, bus_id)

        Session.remove()

        return mv_grid_id

    def get_bus_id_from_mv_grid(self, subst_id):
        """
        Queries the eTraGo bus ID for given MV grid (ding0) ID

        Parameters
        ----------
        subst_id : int
            MV grid (ding0) ID

        Returns
        -------
        int
            eTraGo bus ID

        """

        conn = db.connection(section=self._db_section)
        session_factory = sessionmaker(bind=conn)
        Session = scoped_session(session_factory)
        session = Session()

        bus_id = self._get_bus_id_from_mv_grid(session, subst_id)

        Session.remove()

        return bus_id

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
        self._status_dir = os.path.join(self._json_file["eGo"]["results_dir"], "status")
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

        # Database section
        ego_db = self._db_section
        edisgo_db = edisgo_grid.network.config["db_connection"]["section"]

        if not ego_db == edisgo_db:
            if not self._suppress_log:
                logger.warning(
                    (
                        "eDisGo database configuration (db: '{}') "
                        + "will be overwritten with database configuration "
                        + "from eGo's scenario settings (db: '{}')"
                    ).format(edisgo_db, ego_db)
                )
            edisgo_grid.network.config["db_connection"]["section"] = ego_db

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

        # eTraGo args
        self._etrago_args = self._json_file["eTraGo"]
        self._scn_name = self._etrago_args["scn_name"]
        self._ext_storage = "storage" in self._etrago_args["extendable"]
        if self._ext_storage:
            logger.info("eTraGo Dataset used extendable storage")

        self._pf_post_lopf = self._etrago_args["pf_post_lopf"]

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
        self._db_section = self._edisgo_args["db"]
        self._grid_version = self._edisgo_args["gridversion"]
        self._timesteps_pfa = self._edisgo_args["timesteps_pfa"]
        self._solver = self._edisgo_args["solver"]
        self._grid_path = self._edisgo_args["grid_path"]
        self._choice_mode = self._edisgo_args["choice_mode"]
        self._parallelization = self._edisgo_args["parallelization"]
        self._initial_reinforcement = self._edisgo_args["initial_reinforcement"]
        self._cluster_attributes = self._edisgo_args["cluster_attributes"]
        self._only_cluster = self._edisgo_args["only_cluster"]
        self._max_workers = self._edisgo_args["max_workers"]
        self._max_cos_phi_renewable = self._edisgo_args["max_cos_phi_renewable"]
        self._results = self._edisgo_args["results"]
        self._max_calc_time = self._edisgo_args["max_calc_time"]

        # Some basic checks
        if not self._initial_reinforcement:
            raise NotImplementedError(
                "Skipping the initial reinforcement is not yet implemented"
            )
        if self._only_cluster:
            logger.warning("\n\nThis eDisGo run only returns cluster results\n\n")

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

    def _identify_extended_storages(self):

        conn = db.connection(section=self._db_section)
        session_factory = sessionmaker(bind=conn)
        Session = scoped_session(session_factory)
        session = Session()

        all_mv_grids = self._check_available_mv_grids()

        storages = pd.DataFrame(index=all_mv_grids, columns=["storage_p_nom"])

        logger.info("Identifying extended storage")
        for mv_grid in all_mv_grids:
            bus_id = self._get_bus_id_from_mv_grid(session, mv_grid)

            min_extended = 0.3
            stor_p_nom = self._etrago_network.storage_units.loc[
                (self._etrago_network.storage_units["bus"] == str(bus_id))
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

        Session.remove()

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
            if file.endswith(".pkl"):
                mv_grids.append(
                    int(file.replace("ding0_grids__", "").replace(".pkl", ""))
                )

        return mv_grids

    def _set_grid_choice(self):
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

        if self._choice_mode == "cluster":
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

        elif self._choice_mode == "manual":
            man_grids = self._edisgo_args["manual_grids"]

            choice_df["the_selected_network_id"] = man_grids
            choice_df["no_of_points_per_cluster"] = 1
            choice_df["represented_grids"] = [
                [mv_grid_id] for mv_grid_id in choice_df["the_selected_network_id"]
            ]

            logger.info("Calculating manually chosen MV grids {}".format(man_grids))

        elif self._choice_mode == "all":
            mv_grids = self._check_available_mv_grids()

            choice_df["the_selected_network_id"] = mv_grids
            choice_df["no_of_points_per_cluster"] = 1
            choice_df["represented_grids"] = [
                [mv_grid_id] for mv_grid_id in choice_df["the_selected_network_id"]
            ]

            no_grids = len(mv_grids)
            logger.info("Calculating all available {} MV grids".format(no_grids))

        choice_df = choice_df.sort_values("no_of_points_per_cluster", ascending=False)

        self._grid_choice = choice_df

    def _run_edisgo_pool(self):
        """
        Runs eDisGo for the chosen grids

        """
        parallelization = self._parallelization

        results_dir = os.path.join(self._json_file["eGo"]["results_dir"], self._results)
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
                lambda *xs: xs[1]._run_edisgo(xs[0]),
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
                    edisgo_grid = self._run_edisgo(mv_grid_id)
                    self._edisgo_grids[mv_grid_id] = edisgo_grid
                except Exception as e:
                    self._edisgo_grids[mv_grid_id] = e
                    logger.exception("MV grid {} failed: \n".format(mv_grid_id))
                count += 1

        self._csv_import = self._json_file["eDisGo"]["results"]
        self._save_edisgo_results()
        self._load_edisgo_results()
        self._run_finished = True

    def _run_edisgo(self, mv_grid_id):
        """
        Performs a single eDisGo run

        Parameters
        ----------
        mv_grid_id : int
            MV grid ID of the ding0 grid

        Returns
        -------
        :class:`edisgo.EDisGo`
            Returns the complete eDisGo container, also including results

        """
        self._status_update(mv_grid_id, "start", show=False)

        # ##################### general settings ####################
        config = self._json_file
        engine = get_engine(config=config)
        orm = register_tables_in_saio(engine, config=config)
        scenario = config["eTraGo"]["scn_name"]

        # results directory
        results_dir = os.path.join(
            config["eGo"]["results_dir"], self._results, str(mv_grid_id)
        )
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # logger
        if self._parallelization:
            stream_level = None
        else:
            stream_level = "debug"
        setup_logger(
            loggers=[
                # {"name": "root", "file_level": None, "stream_level": None},
                # {"name": "ego", "file_level": None, "stream_level": None},
                {"name": "edisgo", "file_level": "debug", "stream_level": stream_level},
            ],
            file_name=f"run_edisgo_{mv_grid_id}.log",
            log_dir=results_dir,
        )
        # use edisgo logger in order to have all logging information for one grid go
        # to the same file
        logger = logging.getLogger("edisgo.external.ego._run_edisgo")

        # ################### get requirements from overlying grid ##################
        logger.info(f"MV grid {mv_grid_id}: Calculating interface values.")
        specs = get_etrago_results_per_bus(
            mv_grid_id,
            self._etrago_network,
            self._pf_post_lopf,
            self._max_cos_phi_renewable,
        )

        # ################### start setting up edisgo object ##################
        logger.info(f"MV grid {mv_grid_id}: Initialize MV grid.")
        grid_path = os.path.join(
            config["eGo"]["data_dir"],
            config["eDisGo"]["grid_path"],
            str(mv_grid_id),
        )
        if not os.path.isdir(grid_path):
            msg = f"MV grid {mv_grid_id}: No grid data found."
            logger.error(msg)
            raise Exception(msg)

        # ToDo change back
        # edisgo_grid = import_edisgo_from_files(
        #     edisgo_path=grid_path
        # )
        from edisgo import EDisGo

        edisgo_grid = EDisGo(ding0_grid=grid_path, legacy_ding0_grids=False)
        edisgo_grid.set_timeindex(specs["timeindex"])
        # self._update_edisgo_configs(edisgo_grid)

        # set conventional load time series (active and reactive power)
        edisgo_grid.set_time_series_active_power_predefined(
            conventional_loads_ts="oedb", engine=engine, scenario=scenario
        )
        edisgo_grid.set_time_series_reactive_power_control(
            control="fixed_cosphi",
            generators_parametrisation=None,
            loads_parametrisation="default",
            storage_units_parametrisation=None,
        )
        # ToDo change p_set of conventional loads to peak in time series?

        # ########################### generator data #############################
        logger.info("Set up generator data.")
        # import generator park of future scenario
        edisgo_grid.import_generators(generator_scenario=scenario, engine=engine)

        # set generator time series
        # active power
        edisgo_grid.set_time_series_active_power_predefined(
            dispatchable_generators_ts=specs["dispatchable_generators_active_power"],
            fluctuating_generators_ts=specs["renewables_potential"],
        )
        # reactive power
        if self._pf_post_lopf:
            # ToDo Use eTraGo time series to set reactive power (scale by nominal power)
            edisgo_grid.set_time_series_manual(
                generators_q=specs["generators_reactive_power"].loc[:, []],
            )
            pass
        else:
            edisgo_grid.set_time_series_reactive_power_control(
                control="fixed_cosphi",
                generators_parametrisation="default",
                loads_parametrisation=None,
                storage_units_parametrisation=None,
            )

        # requirements overlying grid
        edisgo_grid.overlying_grid.renewables_curtailment = specs[
            "renewables_curtailment"
        ]

        # check that all generators and conventional loads have time series data
        # ToDo can caplog be used to check for warnings or does it interfere with
        #  logger?
        edisgo_grid.check_integrity()

        # ########################## battery storage ##########################
        logger.info("Set up storage data.")
        # import home storage units
        edisgo_grid.import_home_batteries(scenario=scenario, engine=engine)

        # requirements overlying grid
        edisgo_grid.overlying_grid.storage_units_active_power = specs[
            "storage_units_active_power"
        ]

        # ToDo distribute storage capacity to home storage and large storage (right now
        #  only work around to have storage capacity in the grid)
        edisgo_grid.add_component(
            comp_type="storage_unit",
            bus=edisgo_grid.topology.mv_grid.station.index[0],
            p_nom=specs["storage_units_p_nom"],
            max_hours=specs["storage_units_max_hours"],
            type="large_storage",
        )

        # ################################# DSM ##################################
        # logger.info("Set up DSM data.")
        # dsm_active_power = specs["dsm_active_power"]
        # ToDo: Get DSM potential per load (needs to be added as a function to eDisGo)

        # ####################### district and individual heating #####################
        logger.info("Set up heat supply and demand data.")
        # import heat pumps - also gets heat demand and COP time series per heat pump
        edisgo_grid.import_heat_pumps(scenario=scenario, engine=engine)

        # thermal storage units
        # decentral
        hp_decentral = edisgo_grid.topology.loads_df[
            edisgo_grid.topology.loads_df.sector == "individual_heating"
        ]
        if hp_decentral.empty and specs["thermal_storage_rural_capacity"] > 0:
            raise ValueError(
                "There are thermal storage units for individual heating but no "
                "heat pumps."
            )
        if specs["thermal_storage_rural_capacity"] > 0:
            tes_cap = (
                edisgo_grid.topology.loads_df.loc[hp_decentral.index, "p_set"]
                * specs["thermal_storage_rural_capacity"]
                / edisgo_grid.topology.loads_df.loc[hp_decentral.index, "p_set"].sum()
            )
            # ToDo get efficiency from specs
            edisgo_grid.heat_pump.thermal_storage_units_df = pd.DataFrame(
                data={
                    "capacity": tes_cap,
                    "efficiency": 0.9,
                }
            )
        # district heating
        hp_dh = edisgo_grid.topology.loads_df[
            edisgo_grid.topology.loads_df.sector == "district_heating"
        ]
        if hp_dh.empty and specs["thermal_storage_central_capacity"] > 0:
            raise ValueError(
                "There are thermal storage units for district heating but no "
                "heat pumps."
            )
        if specs["thermal_storage_central_capacity"] > 0:
            tes_cap = (
                edisgo_grid.topology.loads_df.loc[hp_dh.index, "p_set"]
                * specs["thermal_storage_central_capacity"]
                / edisgo_grid.topology.loads_df.loc[hp_dh.index, "p_set"].sum()
            )
            edisgo_grid.heat_pump.thermal_storage_units_df = pd.concat(
                [
                    edisgo_grid.heat_pump.thermal_storage_units_df,
                    pd.DataFrame(
                        data={
                            "capacity": tes_cap,
                            "efficiency": 0.9,
                        }
                    ),
                ]
            )

        # requirements overlying grid
        edisgo_grid.overlying_grid.heat_pump_decentral_active_power = specs[
            "heat_pump_rural_active_power"
        ]
        edisgo_grid.overlying_grid.heat_pump_central_active_power = specs[
            "heat_pump_central_active_power"
        ]
        edisgo_grid.overlying_grid.geothermal_energy_feedin_district_heating = specs[
            "geothermal_energy_feedin_district_heating"
        ]
        edisgo_grid.overlying_grid.solarthermal_energy_feedin_district_heating = specs[
            "solarthermal_energy_feedin_district_heating"
        ]

        # ########################## electromobility ##########################
        logger.info("Set up electromobility data.")
        # import charging points with standing times, etc.
        edisgo_grid.import_electromobility(
            data_source="oedb", scenario=scenario, engine=engine
        )
        # apply charging strategy so that public charging points have a charging
        # time series
        edisgo_grid.apply_charging_strategy(strategy="dumb")
        # get flexibility bands for home and work charging points
        edisgo_grid.electromobility.get_flexibility_bands(
            edisgo_obj=edisgo_grid, use_case=["home", "work"]
        )

        # requirements overlying grid
        edisgo_grid.overlying_grid.electromobility_active_power = specs[
            "electromobility_active_power"
        ]

        # ToDo Malte add intermediate storage of edisgo grid in case of errors later on
        edisgo_grid.save(
            directory=os.path.join(results_dir, "grid_data"),
            save_topology=True,
            save_timeseries=True,
            save_results=False,
            save_electromobility=True,
            # save_dsm=True,
            save_heatpump=True,
            save_overlying_grid=True,
            reduce_memory=True,
            archive=True,
            archive_type="zip",
        )

        # ########################## checks ##########################
        # ToDo Birgit expand
        edisgo_grid.check_integrity()

        # ########################## optimisation ##########################
        # ToDo Maike Call optimisation

        # ########################## reinforcement ##########################
        # edisgo_grid.reinforce()

        # ########################## save results ##########################
        self._status_update(mv_grid_id, "end")
        # edisgo_grid.save(
        #     directory=os.path.join(results_dir, "reinforce_data"),
        #     save_topology=True,
        #     save_timeseries=True,
        #     save_results=True,
        #     save_electromobility=False,
        #     # save_dsm=True,
        #     save_heatpump=False,
        #     save_overlying_grid=False,
        #     reduce_memory=True,
        #     archive=True,
        #     archive_type="zip",
        #     parameters={
        #         "powerflow_results": ["pfa_p", "pfa_q", "v_res"],
        #         "grid_expansion_results": ["grid_expansion_costs", "equipment
        #         _changes"],
        #     },
        # )

        return {edisgo_grid.topology.id: results_dir}

    def _save_edisgo_results(self):
        results_dir = os.path.join(self._json_file["eGo"]["results_dir"], self._results)
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
        results_dir = os.path.join(self._json_file["eGo"]["results_dir"], self._results)
        self._grid_choice = pd.read_csv(
            os.path.join(results_dir, "grid_choice.csv"), index_col=0
        )
        self._grid_choice["represented_grids"] = self._grid_choice.apply(
            lambda x: eval(x["represented_grids"]), axis=1
        )

        for idx, row in self._grid_choice.iterrows():
            mv_grid_id = int(row["the_selected_network_id"])

            try:
                edisgo_grid = import_edisgo_from_files(
                    edisgo_path=os.path.join(self._csv_import, str(mv_grid_id)),
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

    def _get_mv_grid_from_bus_id(self, session, bus_id):
        """
        Queries the MV grid ID for a given eTraGo bus

        Parameters
        ----------
        bus_id : int
            eTraGo bus ID

        Returns
        -------
        int
            MV grid (ding0) ID

        """

        if self._versioned is True:
            ormclass_hvmv_subst = grid.__getattribute__("EgoDpHvmvSubstation")
            subst_id = (
                session.query(ormclass_hvmv_subst.subst_id)
                .filter(
                    ormclass_hvmv_subst.otg_id == bus_id,
                    ormclass_hvmv_subst.version == self._grid_version,
                )
                .scalar()
            )

        if self._versioned is False:
            ormclass_hvmv_subst = model_draft.__getattribute__("EgoGridHvmvSubstation")
            subst_id = (
                session.query(ormclass_hvmv_subst.subst_id)
                .filter(ormclass_hvmv_subst.otg_id == bus_id)
                .scalar()
            )

        return subst_id


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
