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
"""This module contains utility functions for the eGo application.
"""
import csv
import json
import logging
import os
import pandas as pd
import sys
import warnings

from time import localtime, strftime

from sqlalchemy.orm import scoped_session, sessionmaker

if "READTHEDOCS" not in os.environ:
    from egoio.tools import db

logger = logging.getLogger(__name__)


__copyright__ = (
    "Flensburg University of Applied Sciences, "
    "Europa-Universität Flensburg, "
    "Centre for Sustainable Energy Systems"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke"


def define_logging(name):
    """Helps to log your modeling process with eGo and defines all settings.

    Parameters
    ----------
    log_name : str
        Name of log file. Default: ``ego.log``.

    Returns
    -------
    logger : :class:`logging.basicConfig`.
        Set up ``logger`` object of package ``logging``
    """

    # ToDo: Logger should be set up more specific
    #       add pypsa and other logger INFO to ego.log
    now = strftime("%Y-%m-%d_%H%M%S", localtime())

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Logging
    logging.basicConfig(
        stream=sys.stdout, format="%(asctime)s %(message)s", level=logging.INFO
    )

    logger = logging.getLogger(name)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    #    logger = logging.FileHandler(log_name, mode='w')
    fh = logging.FileHandler(log_dir + "/" + name + "_" + now + ".log", mode="w")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def get_scenario_setting(jsonpath=None):
    """Get and open json file with scenaio settings of eGo.
    The settings incluede eGo, eTraGo and eDisGo specific
    settings of arguments and parameters for a reproducible
    calculation.

    Parameters
    ----------
    json_file : str
        Default: ``scenario_setting.json``
        Name of scenario setting json file

    Returns
    -------
    json_file : dict
        Dictionary of json file
    """
    if jsonpath is None:
        path = os.getcwd()
        # add try ego/
        logger.info("Your path is: {}".format(path))
        jsonpath = os.path.join(path, "scenario_setting.json")

    with open(jsonpath) as f:
        json_file = json.load(f)

    # fix remove result_id
    json_file["eGo"].update({"result_id": None})

    # check settings
    if json_file["eGo"]["eTraGo"] is False and json_file["eGo"]["eDisGo"] is False:
        logger.warning(
            "Something went wrong! \n"
            "Please contoll your settings and restart. \n"
            "Set at least eTraGo = true"
        )
        return

    if json_file["eGo"]["eTraGo"] is None and json_file["eGo"]["eDisGo"] is None:
        logger.warning(
            "Something went wrong! \n"
            "Please contoll your settings and restart. \n"
            "Set at least eTraGo = true"
        )
        return

    if json_file["eGo"]["result_id"] and json_file["eGo"]["csv_import_eTraGo"]:
        logger.warning(
            "You set a DB result_id and a csv import path! \n"
            "Please remove on of this settings"
        )
        return
        # or ? json_file['eGo']['result_id'] = None


    if (
        json_file["eGo"]["result_id"] is None
        and json_file["eGo"]["csv_import_eTraGo"] is None
    ):
        logger.info(
            "No data import from results is set \n" "eGo runs by given settings"
        )

    if json_file["eGo"]["csv_import_eTraGo"] and json_file["eGo"]["csv_import_eDisGo"]:
        logger.info("eDisGo and eTraGo results will be imported from csv\n")

    if json_file["eGo"].get("eTraGo") is True:

        logger.info("Using and importing eTraGo settings")

        # special case of SH and model_draft
        # TODO: check and maybe remove this part
        sh_scen = ["SH Status Quo", "SH NEP 2035", "SH eGo 100"]
        if (
            json_file["eTraGo"].get("scn_name") in sh_scen
            and json_file["eTraGo"].get("gridversion") is not None
        ):
            json_file["eTraGo"]["gridversion"] = None

        if json_file["eTraGo"].get("extendable") == "['network', 'storages']":
            json_file["eTraGo"].update({"extendable": ["network", "storage"]})

        if json_file["eTraGo"].get("extendable") == "['network', 'storage']":
            json_file["eTraGo"].update({"extendable": ["network", "storage"]})

        if json_file["eTraGo"].get("extendable") == "['network']":
            json_file["eTraGo"].update({"extendable": ["network"]})

        if json_file["eTraGo"].get("extendable") == "['storages']":
            json_file["eTraGo"].update({"extendable": ["storage"]})

        if json_file["eTraGo"].get("extendable") == "['storage']":
            json_file["eTraGo"].update({"extendable": ["storage"]})

    if json_file["eGo"].get("eDisGo") is True:
        logger.info("Using and importing eDisGo settings")

    if isinstance(json_file["external_config"], str):
        path_external_config = os.path.expanduser(json_file["external_config"])
        logger.info(f"Load external config with path: {path_external_config}")
        with open(path_external_config) as f:
            external_config = json.load(f)
        for key in external_config.keys():
            try:
                json_file[key].update(external_config[key])
            except KeyError:
                json_file[key] = external_config[key]
    else:
        logger.info("Don't load external config.")

    # Serializing json
    json_object = json.dumps(json_file, indent=4)

    # Writing to sample.json
    results_dir = os.path.join(json_file["eGo"]["result_export_path"])
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    with open(os.path.join(results_dir, "config.json"), "w") as outfile:
        outfile.write(json_object)

    return json_file


def fix_leading_separator(csv_file, **kwargs):
    """
    Takes the path to a csv-file. If the first line of this file has a leading
    separator in its header, this field is deleted. If this is done the second
    field of every row is removed, too.
    """
    with open(csv_file, "r") as f:
        lines = csv.reader(f, **kwargs)
        if not lines:
            raise Exception("File %s contained no data" % csv_file)
        first_line = next(lines)
        if first_line[0] == "":
            path, fname = os.path.split(csv_file)
            tmp_file = os.path.join(path, "tmp_" + fname)
            with open(tmp_file, "w+") as out:
                writer = csv.writer(out, **kwargs)
                writer.writerow(first_line[1:])
                for line in lines:
                    line_selection = line[2:]
                    line_selection.insert(0, line[0])
                    writer.writerow(line_selection, **kwargs)
            os.rename(tmp_file, csv_file)


def get_time_steps(json_file):
    """Get time step of calculation by scenario settings.

    Parameters
    ----------
    json_file : :obj:`dict`
        Dictionary of the ``scenario_setting.json`` file

    Returns
    -------
    time_step : int
        Number of timesteps of the calculation.
    """

    end = json_file["eTraGo"].get("end_snapshot")
    start = json_file["eTraGo"].get("start_snapshot")
    time_step = end - start

    return time_step


def open_oedb_session(ego):
    """ """
    _db_section = ego.json_file["eTraGo"]["db"]
    conn = db.connection(section=_db_section)
    session_factory = sessionmaker(bind=conn)
    Session = scoped_session(session_factory)
    session = Session()

    return session


def check_row_consistency(
    df: pd.DataFrame,
    rtol: float = 1e-2,
    atol: float = 1e-4,
    columns: list[str] | None = None,
    reference: str | None = None,
) -> pd.DataFrame:
    """
    Return values within a row that differ by more than the given tolerance.

    Parameters
    ----------
    df : pd.DataFrame
        Data to check, one row per snapshot.
    rtol : float
        Relative tolerance (relative to the reference value).
    atol : float
        Absolute tolerance, avoids false alarms for values near zero.
    columns : list of str, optional
        Columns to compare. Defaults to all columns.
    reference : str, optional
        Column used as the reference. If None, the row median is used.

    Returns
    -------
    pd.DataFrame
        Mismatching rows with their absolute deviation from the reference
        (empty if everything matches).
    """
    data = df[columns] if columns is not None else df

    ref = data[reference] if reference is not None else data.median(axis=1)

    # Deviation of every column from the reference
    dev = data.sub(ref, axis=0).abs()
    tol = atol + rtol * ref.abs()

    # NaN-safe: a NaN in the data counts as a mismatch
    mismatch = dev.gt(tol, axis=0) | data.isna()
    bad_rows = mismatch.any(axis=1)

    return dev[bad_rows]

def check_edisgo_results_per_grid(ego, mv_id, atol = 2e-5, plot=False):
    """
    Checks if etrago results, overlying grid data and edisgo results match for
    one mv grid.

    Parameters
    ----------
    ego : eGo object
        eGo object including etrago and edisgo results
    mv_id : int
        ID of mv grid.
    atol : float, optional
        Allowed maximum absolute deviation. The default is 2e-5.
    plot : boolean, optional
        State if results are plotted. The default is False.

    Returns
    -------
    None.

    """

    edisgo = ego.edisgo.network[mv_id]

    rows_with_diff = {}

    # Check central and decentral heat pumps
    hp_cols = edisgo.topology.loads_df.index[
        edisgo.topology.loads_df.type == "heat_pump"]

    hp_og = (edisgo.overlying_grid.heat_pump_decentral_active_power +
             edisgo.overlying_grid.heat_pump_central_active_power)

    hp_edisgo = (edisgo.timeseries.loads_active_power[hp_cols].sum(axis=1)
                 + edisgo.opf_results.hv_requirement_slacks_t.hp)


    hp_etrago = ego.etrago.disaggregated_network.links[
        ego.etrago.disaggregated_network.links.carrier.str.contains("heat")]

    hp_etrago = hp_etrago[hp_etrago.bus0.str.contains('32377')]

    hp_etrago_ts = ego.etrago.disaggregated_network.links_t.p0.loc[
        :, hp_etrago.index.values].sum(axis=1)

    hp_etrago_ts.index += pd.DateOffset(days=6*366+18*365)

    df_hp = pd.DataFrame(data = {
        "overlying_grid": hp_og.loc[hp_edisgo.index],
        "edisgo": hp_edisgo,
        "etrago": hp_etrago_ts.loc[hp_edisgo.index]
        })

    rows_with_diff["heat_pump"] = check_row_consistency(
        df_hp, reference="edisgo", atol = atol)

    # Check charging points
    cp_cols = edisgo.topology.loads_df.index[
        edisgo.topology.loads_df.type == "charging_point"]

    cp_og = edisgo.overlying_grid.electromobility_active_power

    cp_etrago = ego.etrago.disaggregated_network.links[
        ego.etrago.disaggregated_network.links.carrier.str.contains("charger")]

    cp_etrago = cp_etrago[cp_etrago.bus0.str.contains('32377')]

    cp_etrago_ts = ego.etrago.disaggregated_network.links_t.p0.loc[
        :, cp_etrago.index.values].sum(axis=1)

    cp_etrago_ts.index += pd.DateOffset(days=6*366+18*365)

    df_cp = pd.DataFrame(data = {
        "overlying_grid": cp_og[edisgo.timeseries.loads_active_power.index],
        "edisgo": (edisgo.timeseries.loads_active_power[cp_cols].sum(axis=1)
                   + edisgo.opf_results.hv_requirement_slacks_t.cp),
        "etrago": cp_etrago_ts[hp_edisgo.index]
        })

    rows_with_diff["charging_points"] = check_row_consistency(
        df_cp, reference="edisgo", atol = atol)

    # Check storage dispatch
    sto_og = edisgo.overlying_grid.storage_units_active_power

    df_sto = pd.DataFrame(data = {
        "overlying_grid": sto_og[
            edisgo.timeseries.storage_units_active_power.index],
        "edisgo": (
            edisgo.timeseries.storage_units_active_power.sum(axis=1)
            + edisgo.opf_results.hv_requirement_slacks_t.storage)
        })

    rows_with_diff["storage_disptach"] = check_row_consistency(
        df_sto, reference="edisgo", atol = atol)

    # Check renewable generation
    gens = edisgo.topology.generators_df
    gen_cols = gens.index[gens.type.isin(["solar", "wind"])]

    p_nom_per_carrier = gens.loc[gen_cols].groupby("type").p_nom.sum()

    gen_og = (
        edisgo.overlying_grid.renewables_potential * p_nom_per_carrier.sum()
        ).squeeze() - edisgo.overlying_grid.renewables_curtailment

    df_gen = pd.DataFrame(data = {
        "overlying_grid": gen_og[
            edisgo.timeseries.storage_units_active_power.index],
        "edisgo": (
            edisgo.timeseries.generators_active_power[gen_cols].sum(axis=1)
            - edisgo.opf_results.hv_requirement_slacks_t.curt)
        })

    rows_with_diff["renewable_dispatch"] = check_row_consistency(
        df_gen, reference="edisgo", atol = atol)

    for key in rows_with_diff.keys():
        if not rows_with_diff[key].empty:
            warnings.warn(
            f"The {key} results of eTraGo and eDisGo for mv grid {str(mv_id)} "
            f"exceed tolerance {atol} in {len(rows_with_diff[key])} time steps. ",
            stacklevel=2,
        )

    if plot:
        df_hp.plot(title=f"Heat Pumps {mv_id}")
        df_cp.plot(title=f"Charging points {mv_id}")
        df_sto.plot(title=f"Storage units usage {mv_id}")
        df_gen.plot(title=f"VRES dispatch {mv_id}")

def validate_etrago_edisgo_interface(ego):
    """
    Validates if etrago results, overlying_grid data and edisgo results match.

    Parameters
    ----------
    ego : eGo object
        eGo object including etrago and edisgo results

    Returns
    -------
    None.

    """

    for mv_id in ego.edisgo.network.keys():
        check_edisgo_results_per_grid(ego, mv_id, plot=False)
