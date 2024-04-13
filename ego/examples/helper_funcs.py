from copy import deepcopy
import logging
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt

from edisgo.edisgo import import_edisgo_from_files
from edisgo.flex_opt.reinforce_grid import (
    enhanced_reinforce_grid,
    catch_convergence_reinforce_grid,
)
from edisgo.network.overlying_grid import distribute_overlying_grid_requirements
from edisgo.tools.config import Config
from edisgo.tools.logger import setup_logger
from edisgo.tools.temporal_complexity_reduction import (
    get_most_critical_time_intervals,
)
from edisgo.tools.tools import (
    aggregate_district_heating_components,
    reduce_timeseries_data_to_given_timeindex,
)
from edisgo.io.db import engine
from ego.tools.utilities import get_scenario_setting
from ego.tools.interface import (
    get_etrago_results_per_bus,
    map_etrago_heat_bus_to_district_heating_id,
    rename_generator_carriers_edisgo,
)
from etrago import Etrago


def run_edisgo_task_setup_grid(mv_grid_id, config, scenario):
    """
    Sets up EDisGo object for future scenario (without specifications from overlying
    grid).

    The following data is set up:

    * load time series of conventional loads
    * generator park
    * home storage units
    * DSM data
    * heat pumps including heat demand and COP time series per heat pump
    * charging points with standing times, etc. as well as charging time series for
      uncontrolled charging (done so that public charging points have a charging
      time series) and flexibility bands for home and work charging points

    A dummy time index is set that is later on overwritten by the time index used
    in eTraGo.

    Parameters
    ----------
    mv_grid_id : int
        MV grid ID of the ding0 grid.
    scenario : str
        Name of scenario to import data for. Possible options are "eGon2035"
        and "eGon100RE".
    config : dict
        Dictionary with configuration data.

    Returns
    -------
    :class:`edisgo.EDisGo`

    """
    results_dir = os.path.join(
        config["eDisGo"]["results"], str(mv_grid_id)
    )

    setup_logger(
        loggers=[
            {"name": "edisgo", "file_level": "debug", "stream_level": "debug"},
        ],
        file_name=f"run_edisgo_{mv_grid_id}.log",
        log_dir=results_dir,
    )
    # use edisgo logger in order to have all logging information for one grid go
    # to the same file
    logger = logging.getLogger("edisgo.external.ego._run_edisgo")
    logging.getLogger('pypsa').setLevel(logging.WARNING)

    egon_data_config_yml = os.path.join(
        os.getcwd(), "egon-data.configuration.yaml"
    )
    eng = engine(path=egon_data_config_yml, ssh=True)

    logger.info(f"MV grid {mv_grid_id}: Start task 'setup_grid'.")

    logger.info(f"MV grid {mv_grid_id}: Initialize MV grid.")

    try:
        grid_path = os.path.join(
            config["eDisGo"]["grid_path"],
            str(mv_grid_id),
        )
        if not os.path.isdir(grid_path):
            msg = f"MV grid {mv_grid_id}: No grid data found."
            logger.error(msg)
            raise Exception(msg)

        edisgo_grid = import_edisgo_from_files(edisgo_path=grid_path)
        edisgo_grid.legacy_grids = False
        # overwrite configs
        edisgo_grid._config = Config()
        edisgo_grid.set_timeindex(pd.date_range("1/1/2011", periods=8760, freq="H"))

        logger.info("Set up load time series of conventional loads.")
        edisgo_grid.set_time_series_active_power_predefined(
            conventional_loads_ts="oedb", engine=eng, scenario=scenario
        )
        edisgo_grid.set_time_series_reactive_power_control(
            control="fixed_cosphi",
            generators_parametrisation=None,
            loads_parametrisation="default",
            storage_units_parametrisation=None,
        )
        # overwrite p_set of conventional loads as it changes from scenario to scenario
        edisgo_grid.topology.loads_df[
            "p_set"
        ] = edisgo_grid.timeseries.loads_active_power.max()

        logger.info("Set up generator park.")
        edisgo_grid.import_generators(generator_scenario=scenario, engine=eng)

        logger.info("Set up home storage units.")
        edisgo_grid.import_home_batteries(scenario=scenario, engine=eng)

        logger.info("Set up DSM data.")
        edisgo_grid.import_dsm(scenario=scenario, engine=eng)

        logger.info("Set up heat supply and demand data.")
        edisgo_grid.import_heat_pumps(scenario=scenario, engine=eng)

        logger.info("Set up electromobility data.")
        edisgo_grid.import_electromobility(
            data_source="oedb", scenario=scenario, engine=eng
        )
        # apply charging strategy so that public charging points have a charging
        # time series
        edisgo_grid.apply_charging_strategy(strategy="dumb")
        # get flexibility bands for home and work charging points
        edisgo_grid.electromobility.get_flexibility_bands(
            edisgo_obj=edisgo_grid, use_case=["home", "work"]
        )

        logger.info("Run integrity checks.")
        edisgo_grid.topology.check_integrity()
        edisgo_grid.electromobility.check_integrity()
        edisgo_grid.heat_pump.check_integrity()
        edisgo_grid.dsm.check_integrity()

        edisgo_grid.save(
            directory=os.path.join(results_dir, "grid_data"),
            save_topology=True,
            save_timeseries=True,
            save_results=False,
            save_electromobility=True,
            save_dsm=True,
            save_heatpump=True,
            save_overlying_grid=False,
            reduce_memory=True,
            archive=True,
            archive_type="zip",
        )
    except:
        logger.exception('')


def run_edisgo_task_specs_overlying_grid(
        mv_grid_id, config, scenario,
):
    """
    Gets specifications from overlying grid and integrates them into the EDisGo
    object.

    The following data is set up:

    * set generator time series
    * set up thermal storage units
    * requirements overlying grid on total renewables curtailment, DSM dispatch,
      electromobility charging, heat pump dispatch,

    A dummy time index is set that is later on overwritten by the time index used
    in eTraGo

    Parameters
    ----------
    edisgo_grid : :class:`edisgo.EDisGo`
        EDisGo object.
    scenario : str
        Name of scenario to import data for. Possible options are "eGon2035"
        and "eGon100RE".
    config : dict
        Dictionary with configuration data.

    Returns
    -------
    :class:`edisgo.EDisGo`
        Returns the complete eDisGo container, also including results

    """
    results_dir = os.path.join(
        config["eDisGo"]["results"], str(mv_grid_id)
    )

    setup_logger(
        loggers=[
            {"name": "edisgo", "file_level": "debug", "stream_level": "debug"},
        ],
        file_name=f"run_edisgo_{mv_grid_id}.log",
        log_dir=results_dir,
    )
    # use edisgo logger in order to have all logging information for one grid go
    # to the same file
    logger = logging.getLogger("edisgo.external.ego._run_edisgo")
    logging.getLogger('pypsa').setLevel(logging.WARNING)

    try:
        grid_path = os.path.join(results_dir, "grid_data.zip")
        edisgo_grid = import_edisgo_from_files(
            edisgo_path=grid_path,
            import_topology=True,
            import_timeseries=True,
            import_results=True,
            import_electromobility=True,
            import_heat_pump=True,
            import_dsm=True,
            import_overlying_grid=False,
            from_zip_archive=True,
        )
        edisgo_grid.legacy_grids = False

        logger.info("Start task 'specs_overlying_grid'.")

        logger.info("Get specifications from eTraGo.")
        etrago_path = os.path.join(
            config["eGo"]["csv_import_eTraGo"]
        )
        etrago_network = Etrago(csv_folder_name=etrago_path)

        specs = get_etrago_results_per_bus(
            edisgo_grid.topology.id,
            etrago_network.network,
            pf_post_lopf=False,
            max_cos_phi_ren=None,
        )
        snapshots = specs["timeindex"]

        # get time steps that don't converge in overlying grid
        try:
            convergence = pd.read_csv(
                os.path.join(config["eGo"]["csv_import_eTraGo"], "pf_solution.csv"),
                index_col=0,
                parse_dates=True,
            )
            ts_not_converged = convergence[~convergence.converged].index
        except FileNotFoundError:
            logger.info(
                "No info on converged time steps, wherefore it is assumed that all "
                "converged."
            )
            ts_not_converged = pd.Index([])
        except Exception:
            raise

        # overwrite previously set dummy time index if year that was used differs from
        # year used in etrago
        edisgo_year = edisgo_grid.timeseries.timeindex[0].year
        etrago_year = snapshots[0].year
        if edisgo_year != etrago_year:
            timeindex_new_full = pd.date_range(
                f"1/1/{etrago_year}", periods=8760, freq="H"
            )
            # conventional loads
            edisgo_grid.timeseries.loads_active_power.index = timeindex_new_full
            edisgo_grid.timeseries.loads_reactive_power.index = timeindex_new_full
            # DSM
            edisgo_grid.dsm.e_max.index = timeindex_new_full
            edisgo_grid.dsm.e_min.index = timeindex_new_full
            edisgo_grid.dsm.p_max.index = timeindex_new_full
            edisgo_grid.dsm.p_min.index = timeindex_new_full
            # COP and heat demand
            edisgo_grid.heat_pump.cop_df.index = timeindex_new_full
            edisgo_grid.heat_pump.heat_demand_df.index = timeindex_new_full
            # flexibility bands
            edisgo_grid.electromobility.flexibility_bands[
                "upper_power"
            ].index = timeindex_new_full
            edisgo_grid.electromobility.flexibility_bands[
                "upper_energy"
            ].index = timeindex_new_full
            edisgo_grid.electromobility.flexibility_bands[
                "lower_energy"
            ].index = timeindex_new_full
        # TimeSeries.timeindex
        edisgo_grid.timeseries.timeindex = snapshots

        logger.info("Set generator time series.")
        # rename carrier to match with carrier names in overlying grid
        rename_generator_carriers_edisgo(edisgo_grid)
        # active power
        edisgo_grid.set_time_series_active_power_predefined(
            dispatchable_generators_ts=specs["dispatchable_generators_active_power"],
            fluctuating_generators_ts=specs["renewables_potential"],
        )
        # reactive powe
        edisgo_grid.set_time_series_reactive_power_control(
            control="fixed_cosphi",
            generators_parametrisation="default",
            loads_parametrisation=None,
            storage_units_parametrisation=None,
        )

        # ToDo (medium priority) for now additional optimised storage capacity is
        #  ignored as capacities are very small and optimisation does not offer storage
        #  positioning
        # if specs["storage_units_p_nom"] > 0.3:
        #     logger.info("Set up large battery storage units.")
        #     edisgo_grid.add_component(
        #         comp_type="storage_unit",
        #         bus=edisgo_grid.topology.mv_grid.station.index[0],
        #         p_nom=specs["storage_units_p_nom"],
        #         max_hours=specs["storage_units_max_hours"],
        #         type="large_storage",
        #     )

        logger.info("Set up thermal storage units.")
        # decentral
        hp_decentral = edisgo_grid.topology.loads_df[
            edisgo_grid.topology.loads_df.sector == "individual_heating"
            ]
        if hp_decentral.empty and specs["thermal_storage_rural_capacity"] > 0:
            logger.warning(
                "There are thermal storage units for individual heating but no "
                "heat pumps."
            )
        if not hp_decentral.empty and specs["thermal_storage_rural_capacity"] > 0:
            tes_cap_min_cumsum = (
                edisgo_grid.topology.loads_df.loc[hp_decentral.index, "p_set"]
                .sort_index()
                .cumsum()
            )
            hps_selected = tes_cap_min_cumsum[
                tes_cap_min_cumsum <= specs["thermal_storage_rural_capacity"]
                ].index

            # distribute thermal storage capacity to all selected heat pumps depending
            # on heat pump size
            tes_cap = (
                    edisgo_grid.topology.loads_df.loc[hps_selected, "p_set"]
                    * specs["thermal_storage_rural_capacity"]
                    / edisgo_grid.topology.loads_df.loc[hps_selected, "p_set"].sum()
            )
            edisgo_grid.heat_pump.thermal_storage_units_df = pd.DataFrame(
                data={
                    "capacity": tes_cap,
                    "efficiency": specs["thermal_storage_rural_efficiency"],
                }
            )
        # district heating
        hp_dh = edisgo_grid.topology.loads_df[
            edisgo_grid.topology.loads_df.sector.isin(
                ["district_heating", "district_heating_resistive_heater"]
            )
        ]
        # check if there are as many district heating systems in eTraGo as in eDisGo
        if hp_dh.empty:
            if len(specs["feedin_district_heating"].columns) != 0:
                logger.warning(
                    f"There are {len(hp_dh.area_id.unique())} district heating "
                    f"systems in eDisGo and "
                    f"{len(specs['feedin_district_heating'].columns)} in eTraGo."
                )
        else:
            if len(hp_dh.area_id.unique()) != len(
                    specs["feedin_district_heating"].columns
            ):
                logger.warning(
                    f"There are {len(hp_dh.area_id.unique())} district heating "
                    f"systems in eDisGo and "
                    f"{len(specs['feedin_district_heating'].columns)} in eTraGo."
                )
            # check that installed PtH capacity is equal in eTraGo as in eDisGo
            if abs(hp_dh.p_set.sum() - specs["heat_pump_central_p_nom"]) > 1e-3:
                logger.warning(
                    f"Installed capacity of PtH units in district heating differs "
                    f"between eTraGo ({specs['heat_pump_central_p_nom']} MW) and "
                    f"eDisGo ({hp_dh.p_set.sum()} MW)."
                )

            if not specs["feedin_district_heating"].empty:

                # map district heating ID to heat bus ID from eTraGo
                if scenario.split("_")[-1] == "lowflex":
                    scn = scenario.split("_")[0]
                else:
                    scn = scenario
                egon_data_config_yml = os.path.join(
                    os.getcwd(), "egon-data.configuration.yaml"
                )
                eng = engine(path=egon_data_config_yml, ssh=True)
                map_etrago_heat_bus_to_district_heating_id(specs, scn, eng)

                for dh_id in hp_dh.district_heating_id.unique():
                    if dh_id in specs["thermal_storage_central_capacity"].index:
                        if specs["thermal_storage_central_capacity"].at[dh_id] > 0:
                            # get PtH unit name to allocate thermal storage unit to
                            comp_name = hp_dh[hp_dh.district_heating_id == dh_id].index[
                                0
                            ]
                            edisgo_grid.heat_pump.thermal_storage_units_df = pd.concat(
                                [
                                    edisgo_grid.heat_pump.thermal_storage_units_df,
                                    pd.DataFrame(
                                        data={
                                            "capacity": specs[
                                                "thermal_storage_central_capacity"
                                            ].at[dh_id],
                                            "efficiency": specs[
                                                "thermal_storage_central_efficiency"
                                            ],
                                        },
                                        index=[comp_name],
                                    ),
                                ]
                            )

        logger.info("Set requirements from overlying grid.")
        # all time series from overlying grid are also kept for low flex scenarios
        # in order to afterwards check difference in dispatch between eTraGo and eDisGo

        # curtailment
        # scale curtailment by ratio of nominal power in eDisGo and eTraGo
        for carrier in specs["renewables_curtailment"].columns:
            p_nom_total = specs["renewables_p_nom"][carrier]
            p_nom_mv_lv = edisgo_grid.topology.generators_df[
                edisgo_grid.topology.generators_df["type"] == carrier
                ].p_nom.sum()
            specs["renewables_curtailment"][carrier] *= p_nom_mv_lv / p_nom_total
        # check that curtailment does not exceed feed-in (for all converged time steps)
        vres_gens = edisgo_grid.topology.generators_df[
            edisgo_grid.topology.generators_df["type"].isin(
                specs["renewables_curtailment"].columns
            )
        ].index
        pot_vres_gens = edisgo_grid.timeseries.generators_active_power.loc[
                        :, vres_gens
                        ].sum(axis=1)
        pot_vres_gens.loc[ts_not_converged] = 0.0
        total_curtailment = specs["renewables_curtailment"].loc[:].sum(axis=1)
        total_curtailment.loc[ts_not_converged] = 0.0
        diff = pot_vres_gens - total_curtailment
        if (diff < 0).any():
            # if curtailment is much larger than feed-in, throw an error
            if (diff < -1e-3).any():
                raise ValueError("Curtailment exceeds feed-in!")
            # if curtailment is only slightly larger than feed-in, this is due to
            # numerical errors and therefore corrected
            else:
                ts_neg_curtailment = diff[(diff < 0)].index
                total_curtailment.loc[ts_neg_curtailment] += diff.loc[
                    ts_neg_curtailment
                ]
        edisgo_grid.overlying_grid.renewables_curtailment = total_curtailment

        # battery storage
        # scale storage time series by ratio of nominal power in eDisGo and eTraGo
        p_nom_total = specs["storage_units_p_nom"]
        p_nom_mv_lv = edisgo_grid.topology.storage_units_df.p_nom.sum()
        edisgo_grid.overlying_grid.storage_units_active_power = (
                specs["storage_units_active_power"] * p_nom_mv_lv / p_nom_total
        )
        edisgo_grid.overlying_grid.storage_units_soc = specs["storage_units_soc"]

        # DSM
        edisgo_grid.overlying_grid.dsm_active_power = specs["dsm_active_power"]

        # BEV
        edisgo_grid.overlying_grid.electromobility_active_power = specs[
            "electromobility_active_power"
        ]

        # PtH
        # scale heat pump time series by ratio of nominal power in eDisGo and eTraGo
        p_nom_total = specs["heat_pump_rural_p_nom"]
        p_nom_mv_lv = edisgo_grid.topology.loads_df[
            edisgo_grid.topology.loads_df.sector.isin(
                ["individual_heating", "individual_heating_resistive_heater"]
            )
        ].p_set.sum()
        edisgo_grid.overlying_grid.heat_pump_decentral_active_power = (
                specs["heat_pump_rural_active_power"] * p_nom_mv_lv / p_nom_total
        )
        p_nom_total = specs["heat_pump_central_p_nom"]
        p_nom_mv_lv = edisgo_grid.topology.loads_df[
            edisgo_grid.topology.loads_df.sector.isin(
                ["district_heating", "district_heating_resistive_heater"]
            )
        ].p_set.sum()
        edisgo_grid.overlying_grid.heat_pump_central_active_power = (
                specs["heat_pump_central_active_power"] * p_nom_mv_lv / p_nom_total
        )

        # Other feed-in into district heating
        edisgo_grid.overlying_grid.feedin_district_heating = specs[
            "feedin_district_heating"
        ]

        # Thermal storage units SoC
        edisgo_grid.overlying_grid.thermal_storage_units_decentral_soc = specs[
            "thermal_storage_rural_soc"
        ]
        edisgo_grid.overlying_grid.thermal_storage_units_central_soc = specs[
            "thermal_storage_central_soc"
        ]

        # Delete some flex data in case of low flex scenario
        if scenario in ["eGon2035_lowflex", "eGon100RE_lowflex"]:
            # delete DSM and flexibility bands to save disk space
            edisgo_grid.dsm = edisgo_grid.dsm.__class__()
            edisgo_grid.electromobility.flexibility_bands = {
                "upper_power": pd.DataFrame(),
                "lower_energy": pd.DataFrame(),
                "upper_energy": pd.DataFrame(),
            }

        logger.info("Run integrity check.")
        edisgo_grid.check_integrity()

        zip_name = "grid_data_overlying_grid"
        if scenario in ["eGon2035_lowflex", "eGon100RE_lowflex"]:
            zip_name += "_lowflex"
        edisgo_grid.save(
            directory=os.path.join(results_dir, zip_name),
            save_topology=True,
            save_timeseries=True,
            save_results=True,
            save_electromobility=True,
            save_dsm=True,
            save_heatpump=True,
            save_overlying_grid=True,
            reduce_memory=True,
            archive=True,
            archive_type="zip",
            parameters={"grid_expansion_results": ["equipment_changes"]},
        )
    except:
        logger.exception('')


def run_temporal_complexity_reduction(mv_grid_id, config):

    results_dir = os.path.join(
        config["eDisGo"]["results"], str(mv_grid_id)
    )

    setup_logger(
        loggers=[
            {"name": "edisgo", "file_level": "debug", "stream_level": "debug"},
        ],
        file_name=f"run_edisgo_{mv_grid_id}.log",
        log_dir=results_dir,
    )
    # use edisgo logger in order to have all logging information for one grid go
    # to the same file
    logger = logging.getLogger("edisgo.external.ego._run_edisgo")
    logging.getLogger('pypsa').setLevel(logging.WARNING)

    grid_path = os.path.join(results_dir, "grid_data_overlying_grid.zip")
    edisgo_grid = import_edisgo_from_files(
        edisgo_path=grid_path,
        import_topology=True,
        import_timeseries=True,
        import_results=False,
        import_electromobility=True,
        import_heat_pump=True,
        import_dsm=True,
        import_overlying_grid=True,
        from_zip_archive=True,
    )
    edisgo_grid.legacy_grids = False

    logger.info("Start task 'temporal complexity reduction'.")

    # get non-converging time steps
    try:
        convergence = pd.read_csv(
            os.path.join(config["eGo"]["csv_import_eTraGo"], "pf_solution.csv"),
            index_col=0,
            parse_dates=True,
        )
        ts_not_converged = convergence[~convergence.converged].index
    except FileNotFoundError:
        logger.info(
            "No info on converged time steps, wherefore it is assumed that all "
            "converged."
        )
        ts_not_converged = []
    except Exception:
        raise

    # set time series data at time steps with non-convergence issues to zero
    if len(ts_not_converged) > 0:
        logger.info(
            f"{len(ts_not_converged)} time steps did not converge in overlying "
            f"grid. Time series data at time steps with non-convergence issues is "
            f"set to zero."
        )
        # set data in TimeSeries object to zero
        attributes = edisgo_grid.timeseries._attributes
        for attr in attributes:
            ts = getattr(edisgo_grid.timeseries, attr)
            if not ts.empty:
                ts.loc[ts_not_converged, :] = 0
                setattr(edisgo_grid.timeseries, attr, ts)
        # set data in OverlyingGrid object to zero
        attributes = edisgo_grid.overlying_grid._attributes
        for attr in attributes:
            ts = getattr(edisgo_grid.overlying_grid, attr)
            if not ts.empty and "soc" not in attr:
                if isinstance(ts, pd.Series):
                    ts.loc[ts_not_converged] = 0
                else:
                    ts.loc[ts_not_converged, :] = 0
                setattr(edisgo_grid.overlying_grid, attr, ts)

    # distribute overlying grid data
    logger.info("Distribute overlying grid data.")
    edisgo_grid = distribute_overlying_grid_requirements(edisgo_grid)

    # get critical time intervals
    time_intervals = get_most_critical_time_intervals(
        edisgo_grid,
        percentage=1.0,
        time_steps_per_time_interval=168,
        time_step_day_start=4,
        save_steps=True,
        path=results_dir,
        use_troubleshooting_mode=True,
        overloading_factor=0.95,
        voltage_deviation_factor=0.95,
    )

    # drop time intervals with non-converging time steps
    if len(ts_not_converged) > 0:

        # check overloading time intervals
        for ti in time_intervals.index:
            # check if there is one time step in time interval that did not converge
            non_converged_ts_in_ti = [
                _
                for _ in ts_not_converged
                if _ in time_intervals.at[ti, "time_steps_overloading"]
            ]
            if len(non_converged_ts_in_ti) > 0:
                # if any time step did not converge, set time steps to None
                time_intervals.at[ti, "time_steps_overloading"] = None

        # check voltage issues time intervals
        for ti in time_intervals.index:
            # check if there is one time step in time interval that did not converge
            non_converged_ts_in_ti = [
                _
                for _ in ts_not_converged
                if _ in time_intervals.at[ti, "time_steps_voltage_issues"]
            ]
            if len(non_converged_ts_in_ti) > 0:
                # if any time step did not converge, set time steps to None
                time_intervals.at[ti, "time_steps_voltage_issues"] = None

    # select time intervals
    if not time_intervals.loc[:, "time_steps_overloading"].dropna().empty:
        tmp = time_intervals.loc[:, "time_steps_overloading"].dropna()
        time_interval_1 = tmp.iloc[0]
        time_interval_1_ind = tmp.index[0]
    else:
        time_interval_1 = pd.Index([])
        time_interval_1_ind = None
    if not time_intervals.loc[:, "time_steps_voltage_issues"].dropna().empty:
        tmp = time_intervals.loc[:, "time_steps_voltage_issues"].dropna()
        time_interval_2 = tmp.iloc[0]
        time_interval_2_ind = tmp.index[0]
    else:
        time_interval_2 = pd.Index([])
        time_interval_2_ind = None

    # check if time intervals overlap
    overlap = [_ for _ in time_interval_1 if _ in time_interval_2]
    if len(overlap) > 0:
        logger.info(
            "Selected time intervals overlap. Trying to find another "
            "time interval in voltage_issues intervals."
        )
        # check if time interval without overlap can be found
        for ti in time_intervals.loc[:, "time_steps_voltage_issues"].dropna().index:
            overlap = [
                _
                for _ in time_interval_1
                if _ in time_intervals.at[ti, "time_steps_voltage_issues"]
            ]
            if len(overlap) == 0:
                time_interval_2 = time_intervals.at[ti, "time_steps_voltage_issues"]
                time_interval_2_ind = ti
                break
    overlap = [_ for _ in time_interval_1 if _ in time_interval_2]
    if len(overlap) > 0:
        logger.info(
            "Selected time intervals overlap. Trying to find another "
            "time interval in overloading intervals."
        )
        # check if time interval without overlap can be found
        for ti in time_intervals.loc[:, "time_steps_overloading"].dropna().index:
            overlap = [
                _
                for _ in time_interval_2
                if _ in time_intervals.at[ti, "time_steps_overloading"]
            ]
            if len(overlap) == 0:
                time_interval_1 = time_intervals.at[ti, "time_steps_overloading"]
                time_interval_1_ind = ti
                break

    overlap = [_ for _ in time_interval_1 if _ in time_interval_2]
    if len(overlap) > 0:
        logger.info(
            "Overlap of selected time intervals cannot be avoided. "
            "Time intervals are therefore concatenated."
        )
        time_interval_1 = (
            time_interval_1.append(time_interval_2).unique().sort_values()
        )
        time_interval_2 = None

    # save to csv
    percentage = pd.Series()
    percentage["time_interval_1"] = (
        None
        if time_interval_1_ind is None
        else time_intervals.at[
            time_interval_1_ind, "percentage_max_overloaded_components"
        ]
    )
    percentage["time_interval_2"] = (
        None
        if time_interval_2_ind is None
        else time_intervals.at[
            time_interval_2_ind, "percentage_buses_max_voltage_deviation"
        ]
    )
    pd.DataFrame(
        {
            "time_steps": [time_interval_1, time_interval_2],
            "percentage": percentage,
        },
        index=["time_interval_1", "time_interval_2"],
    ).to_csv(os.path.join(results_dir, "selected_time_intervals.csv"))


def run_temporal_complexity_reduction_new(mv_grid_id, config):

    def get_min_max_intervals(grid_obj, what):
        comps_ts = grid_obj.timeseries.residual_load
        if what == "max":
            timesteps = comps_ts.rolling(
                window=int(time_steps_per_time_interval), closed="right"
            ).max()
        else:
            timesteps = comps_ts.rolling(
                window=int(time_steps_per_time_interval), closed="right"
            ).min()
        # drop each time interval that doesn't start at specified hour of the day
        timesteps = timesteps.iloc[
                    time_step_day_start:: time_steps_per_day].dropna()
        # move time index back, as rolling window gives end point of time interval, but
        # we want start point
        timesteps.index = timesteps.index - pd.DateOffset(
            hours=int(time_steps_per_time_interval)
        )
        return timesteps

    def plotting():
        fig, ax = plt.subplots(figsize=(15, 5))
        time_intervals_values_df.plot(ax=ax)
        figpath = os.path.join(results_dir, f"time_intervals_residual_load.png")
        plt.savefig(figpath, dpi=150, bbox_inches='tight', pad_inches=0.1)
        plt.close()

    time_steps_per_time_interval = 168
    time_step_day_start = 4
    time_steps_per_day = 24

    results_dir = os.path.join(
        config["eDisGo"]["results"], str(mv_grid_id)
    )

    setup_logger(
        loggers=[
            {"name": "edisgo", "file_level": "debug", "stream_level": "debug"},
        ],
        file_name=f"run_edisgo_{mv_grid_id}.log",
        log_dir=results_dir,
    )
    # use edisgo logger in order to have all logging information for one grid go
    # to the same file
    logger = logging.getLogger("edisgo.external.ego._run_edisgo")
    logging.getLogger('pypsa').setLevel(logging.WARNING)

    try:
        grid_path = os.path.join(results_dir, "grid_data_overlying_grid.zip")
        edisgo_grid = import_edisgo_from_files(
            edisgo_path=grid_path,
            import_topology=True,
            import_timeseries=True,
            import_results=False,
            import_electromobility=True,
            import_heat_pump=True,
            import_dsm=True,
            import_overlying_grid=True,
            from_zip_archive=True,
        )
        edisgo_grid.legacy_grids = False

        grid_path = os.path.join(results_dir, "grid_data_overlying_grid_lowflex.zip")
        edisgo_grid_lowflex = import_edisgo_from_files(
            edisgo_path=grid_path,
            import_topology=True,
            import_timeseries=True,
            import_results=False,
            import_electromobility=True,
            import_heat_pump=True,
            import_dsm=True,
            import_overlying_grid=True,
            from_zip_archive=True,
        )
        edisgo_grid_lowflex.legacy_grids = False

        logger.info("Start task 'temporal complexity reduction'.")

        # get non-converging time steps
        try:
            convergence = pd.read_csv(
                os.path.join(config["eGo"]["csv_import_eTraGo"], "pf_solution.csv"),
                index_col=0,
                parse_dates=True,
            )
            ts_not_converged = convergence[~convergence.converged].index
        except FileNotFoundError:
            logger.info(
                "No info on converged time steps, wherefore it is assumed that all "
                "converged."
            )
            ts_not_converged = []
        except Exception:
            raise

        # set time series data at time steps with non-convergence issues to zero
        if len(ts_not_converged) > 0:
            logger.info(
                f"{len(ts_not_converged)} time steps did not converge in overlying "
                f"grid. Time series data at time steps with non-convergence issues is "
                f"set to zero."
            )
            # set data in TimeSeries object to zero
            attributes = edisgo_grid.timeseries._attributes
            for attr in attributes:
                ts = getattr(edisgo_grid.timeseries, attr)
                if not ts.empty:
                    ts.loc[ts_not_converged, :] = 0
                    setattr(edisgo_grid.timeseries, attr, ts)
            # set data in OverlyingGrid object to zero
            attributes = edisgo_grid.overlying_grid._attributes
            for attr in attributes:
                ts = getattr(edisgo_grid.overlying_grid, attr)
                if not ts.empty and "soc" not in attr:
                    if isinstance(ts, pd.Series):
                        ts.loc[ts_not_converged] = 0
                    else:
                        ts.loc[ts_not_converged, :] = 0
                    setattr(edisgo_grid.overlying_grid, attr, ts)

        # distribute overlying grid data
        logger.info("Distribute overlying grid data.")
        edisgo_grid = distribute_overlying_grid_requirements(edisgo_grid)
        edisgo_grid_lowflex = distribute_overlying_grid_requirements(edisgo_grid_lowflex)

        # get critical time intervals
        time_intervals_values_df = pd.DataFrame()
        time_intervals_values_df["full_flex_max"] = get_min_max_intervals(
            edisgo_grid,"max"
        )
        time_intervals_values_df["full_flex_min"] = get_min_max_intervals(
            edisgo_grid, "min"
        )
        time_intervals_values_df["low_flex_max"] = get_min_max_intervals(
            edisgo_grid_lowflex,"max"
        )
        time_intervals_values_df["low_flex_min"] = get_min_max_intervals(
            edisgo_grid_lowflex, "min"
        )

        # save plot
        plotting()

        # set to zero if minimal residual load is positive or if it's absolute value is
        # much smaller than maximum residual load
        for col in ["full_flex_min", "low_flex_min"]:
            min_res_load = time_intervals_values_df[col].min()
            max_res_load = time_intervals_values_df[
                "full_flex_max"].max() if col == "full_flex_min" else \
            time_intervals_values_df["low_flex_max"].max()
            if min_res_load > 0:
                time_intervals_values_df[col] = 0.0
            elif abs(min_res_load) / abs(max_res_load) < 0.2:
                time_intervals_values_df[col] = 0.0
        # set to zero if maximum residual load is negative or if it's absolute value is
        # much smaller than inimum residual load
        for col in ["full_flex_max", "low_flex_max"]:
            max_res_load = time_intervals_values_df[col].max()
            min_res_load = time_intervals_values_df[
                "full_flex_min"].min() if col == "full_flex_max" else \
            time_intervals_values_df["low_flex_min"].min()
            if max_res_load < 0:
                time_intervals_values_df[col] = 0.0
            elif abs(max_res_load) / abs(min_res_load) < 0.2:
                time_intervals_values_df[col] = 0.0

        # get time intervals with highest values
        final_time_intervals = pd.DataFrame(columns=["time_steps", "value"])
        for col in time_intervals_values_df.columns:
            if not (time_intervals_values_df[col] == 0.0).all():
                if col in ["full_flex_min", "low_flex_min"]:
                    ti_start = time_intervals_values_df[col].idxmin()
                    value = time_intervals_values_df[col].min()
                else:
                    ti_start = time_intervals_values_df[col].idxmax()
                    value = time_intervals_values_df[col].max()
                final_time_intervals.at[col, "time_steps"] = pd.date_range(
                    start=ti_start,
                    periods=time_steps_per_time_interval,
                    freq="H"
                )
                final_time_intervals.at[col, "value"] = value

        def check_overlap(base, col):
            if col in final_time_intervals.index:
                overlap = [_ for _ in final_time_intervals.at[base, "time_steps"]
                           if _ in final_time_intervals.at[col, "time_steps"]]
                if len(overlap) > 0:
                    if len(overlap) < time_steps_per_time_interval:
                        # if time intervals partly overlap, combine them
                        final_time_intervals.at[base, "time_steps"] = (
                            (pd.Index(final_time_intervals.at[base, "time_steps"]).append(
                                pd.Index(final_time_intervals.at[
                                             col, "time_steps"]))).unique().sort_values()
                        )
                        final_time_intervals.at[col, "time_steps"] = None
                    else:
                        # if time intervals fully overlap, delete one
                        final_time_intervals.at[col, "time_steps"] = None

        # check overlap for full_flex_max
        base = "full_flex_max"
        # make sure time interval exists
        if base in final_time_intervals.index:
            # make sure time intervals are not None
            if final_time_intervals.at[base, "time_steps"] is not None:
                for col in ["full_flex_min", "low_flex_max", "low_flex_min"]:
                    if col in final_time_intervals.index:
                        if final_time_intervals.at[col, "time_steps"] is not None:
                            check_overlap(base, col)
        # check overlap for full_flex_min
        base = "full_flex_min"
        # make sure time interval exists
        if base in final_time_intervals.index:
            # make sure time intervals are not None
            if final_time_intervals.at[base, "time_steps"] is not None:
                for col in ["low_flex_max", "low_flex_min"]:
                    if col in final_time_intervals.index:
                        if final_time_intervals.at[col, "time_steps"] is not None:
                            check_overlap(base, col)
        # check overlap for low_flex_max
        base = "low_flex_max"
        # make sure time interval exists
        if base in final_time_intervals.index:
            # make sure time intervals are not None
            if final_time_intervals.at[base, "time_steps"] is not None:
                for col in ["low_flex_min"]:
                    if col in final_time_intervals.index:
                        if final_time_intervals.at[col, "time_steps"] is not None:
                            check_overlap(base, col)

        # # drop time intervals with non-converging time steps
        # if len(ts_not_converged) > 0:
        #
        #     # check overloading time intervals
        #     for ti in time_intervals.index:
        #         # check if there is one time step in time interval that did not converge
        #         non_converged_ts_in_ti = [
        #             _
        #             for _ in ts_not_converged
        #             if _ in time_intervals.at[ti, "time_steps_overloading"]
        #         ]
        #         if len(non_converged_ts_in_ti) > 0:
        #             # if any time step did not converge, set time steps to None
        #             time_intervals.at[ti, "time_steps_overloading"] = None
        #
        #     # check voltage issues time intervals
        #     for ti in time_intervals.index:
        #         # check if there is one time step in time interval that did not converge
        #         non_converged_ts_in_ti = [
        #             _
        #             for _ in ts_not_converged
        #             if _ in time_intervals.at[ti, "time_steps_voltage_issues"]
        #         ]
        #         if len(non_converged_ts_in_ti) > 0:
        #             # if any time step did not converge, set time steps to None
        #             time_intervals.at[ti, "time_steps_voltage_issues"] = None

        # save to csv
        final_time_intervals.to_csv(
            os.path.join(results_dir, "selected_time_intervals_new.csv")
        )
    except:
        logger.exception('')


def run_edisgo_task_optimisation(mv_grid_id, config, scenario):
    """
    Runs the dispatch optimisation.

    """
    results_dir = os.path.join(
        config["eDisGo"]["results"], str(mv_grid_id)
    )

    setup_logger(
        loggers=[
            {"name": "edisgo", "file_level": "debug", "stream_level": "debug"},
        ],
        file_name=f"run_edisgo_{mv_grid_id}.log",
        log_dir=results_dir,
    )
    # use edisgo logger in order to have all logging information for one grid go
    # to the same file
    logger = logging.getLogger("edisgo.external.ego._run_edisgo")
    logging.getLogger('pypsa').setLevel(logging.WARNING)

    try:
        if scenario in ["eGon2035", "eGon100RE"]:
            zip_name = "grid_data_overlying_grid.zip"
        else:
            zip_name = "grid_data_overlying_grid_lowflex.zip"
        grid_path = os.path.join(results_dir, zip_name)
        edisgo_grid = import_edisgo_from_files(
            edisgo_path=grid_path,
            import_topology=True,
            import_timeseries=True,
            import_results=False,
            import_electromobility=True,
            import_heat_pump=True,
            import_dsm=True,
            import_overlying_grid=True,
            from_zip_archive=True,
        )
        edisgo_grid.legacy_grids = False

        time_intervals = pd.read_csv(
            os.path.join(results_dir, "selected_time_intervals_new.csv"),
            index_col=0,
        )
        for ti in time_intervals.index:
            time_steps = time_intervals.at[ti, "time_steps"]
            if time_steps is not np.nan:
                time_intervals.at[ti, "time_steps"] = pd.date_range(
                    start=time_steps.split("'")[1],
                    end=time_steps.split("'")[-2],
                    freq="h",
                )
            else:
                time_intervals.at[ti, "time_steps"] = None

        logger.info("Start task 'optimisation'.")

        # prepare district heating data
        # make sure district heating ID is string of integer not float
        columns_rename = [
            str(int(float(_)))
            for _ in edisgo_grid.overlying_grid.feedin_district_heating.columns
        ]
        if len(columns_rename) > 0:
            edisgo_grid.overlying_grid.feedin_district_heating.columns = columns_rename
        cols = edisgo_grid.overlying_grid.thermal_storage_units_central_soc.columns
        columns_rename = [str(int(float(_))) for _ in cols]
        if len(columns_rename) > 0:
            edisgo_grid.overlying_grid.thermal_storage_units_central_soc.columns = (
                columns_rename
            )
        # aggregate PtH units in same district heating network and subtract feed-in
        # from other heat sources from heat demand in district heating network
        aggregate_district_heating_components(
            edisgo_grid,
            feedin_district_heating=edisgo_grid.overlying_grid.feedin_district_heating,
        )
        # apply operating strategy so that inflexible heat pumps (without heat
        # storage units) have a time series
        edisgo_grid.apply_heat_pump_operating_strategy()

        timeindex = pd.Index([])
        for ti in time_intervals.index:
            time_steps = time_intervals.at[ti, "time_steps"]
            if time_steps is None:
                continue
            else:
                timeindex = timeindex.append(pd.Index(time_steps))
                # copy edisgo object
                edisgo_copy = deepcopy(edisgo_grid)
                # temporal complexity reduction
                reduce_timeseries_data_to_given_timeindex(edisgo_copy, time_steps)

                # spatial complexity reduction
                edisgo_copy.spatial_complexity_reduction(
                    mode="kmeansdijkstra",
                    cluster_area="feeder",
                    reduction_factor=0.3,
                    reduction_factor_not_focused=False,
                )

                # OPF
                # flexibilities in full flex: DSM, decentral and central PtH units,
                # curtailment, EVs, storage units
                # flexibilities in low flex: curtailment, storage units
                psa_net = edisgo_copy.to_pypsa()
                if scenario in ["eGon2035", "eGon100RE"]:
                    flexible_loads = edisgo_copy.dsm.p_max.columns
                    # flexible_hps = (
                    #     edisgo_copy.heat_pump.thermal_storage_units_df.index.values
                    # )
                    flexible_cps = psa_net.loads.loc[
                        psa_net.loads.index.str.contains("home")
                        | (psa_net.loads.index.str.contains("work"))
                    ].index.values
                else:
                    flexible_loads = []
                    # flexible_hps = []
                    flexible_cps = []
                flexible_hps = edisgo_copy.heat_pump.heat_demand_df.columns.values
                flexible_storage_units = (
                    edisgo_copy.topology.storage_units_df.index.values
                )

                edisgo_copy.pm_optimize(
                    flexible_cps=flexible_cps,
                    flexible_hps=flexible_hps,
                    flexible_loads=flexible_loads,
                    flexible_storage_units=flexible_storage_units,
                    s_base=1,
                    opf_version=4,
                    silence_moi=False,
                    method="soc",
                )

                # save OPF results
                zip_name = f"opf_results_{ti}"
                if scenario in ["eGon2035_lowflex", "eGon100RE_lowflex"]:
                    zip_name += "_lowflex"
                edisgo_copy.save(
                    directory=os.path.join(results_dir, zip_name),
                    save_topology=True,
                    save_timeseries=False,
                    save_results=False,
                    save_opf_results=True,
                    reduce_memory=True,
                    archive=True,
                    archive_type="zip",
                )

                # write flexibility dispatch results to spatially unreduced edisgo
                # object
                edisgo_grid.timeseries._loads_active_power.loc[
                    time_steps, :
                ] = edisgo_copy.timeseries.loads_active_power
                edisgo_grid.timeseries._loads_reactive_power.loc[
                    time_steps, :
                ] = edisgo_copy.timeseries.loads_reactive_power
                edisgo_grid.timeseries._generators_active_power.loc[
                    time_steps, :
                ] = edisgo_copy.timeseries.generators_active_power
                edisgo_grid.timeseries._generators_reactive_power.loc[
                    time_steps, :
                ] = edisgo_copy.timeseries.generators_reactive_power

                try:
                    edisgo_grid.timeseries._storage_units_active_power
                except AttributeError:
                    edisgo_grid.timeseries.storage_units_active_power = pd.DataFrame(
                        index=edisgo_grid.timeseries.timeindex
                    )
                edisgo_grid.timeseries._storage_units_active_power.loc[
                    time_steps,
                    edisgo_copy.timeseries.storage_units_active_power.columns,
                ] = edisgo_copy.timeseries.storage_units_active_power
                try:
                    edisgo_grid.timeseries._storage_units_reactive_power
                except AttributeError:
                    edisgo_grid.timeseries.storage_units_reactive_power = pd.DataFrame(
                        index=edisgo_grid.timeseries.timeindex
                    )
                edisgo_grid.timeseries._storage_units_reactive_power.loc[
                    time_steps,
                    edisgo_copy.timeseries.storage_units_reactive_power.columns,
                ] = edisgo_copy.timeseries.storage_units_reactive_power

                # write OPF results back
                edisgo_grid.opf_results.overlying_grid = pd.concat(
                    [
                        edisgo_grid.opf_results.overlying_grid,
                        edisgo_copy.opf_results.overlying_grid,
                    ]
                )
                edisgo_grid.opf_results.battery_storage_t.p = pd.concat(
                    [
                        edisgo_grid.opf_results.battery_storage_t.p,
                        edisgo_copy.opf_results.battery_storage_t.p,
                    ]
                )
                edisgo_grid.opf_results.battery_storage_t.e = pd.concat(
                    [
                        edisgo_grid.opf_results.battery_storage_t.e,
                        edisgo_copy.opf_results.battery_storage_t.e,
                    ]
                )

        edisgo_grid.timeseries.timeindex = timeindex

        zip_name = "grid_data_optimisation"
        if scenario in ["eGon2035_lowflex", "eGon100RE_lowflex"]:
            zip_name += "_lowflex"
        edisgo_grid.save(
            directory=os.path.join(results_dir, zip_name),
            save_topology=True,
            save_timeseries=True,
            save_results=False,
            save_opf_results=True,
            save_electromobility=False,
            save_dsm=False,
            save_heatpump=False,
            save_overlying_grid=False,
            reduce_memory=True,
            archive=True,
            archive_type="zip",
        )
    except:
        logger.exception('')


def run_edisgo_task_grid_reinforcement(mv_grid_id, config, scenario):
    """
    Runs the grid reinforcement.

    """
    results_dir = os.path.join(
        config["eDisGo"]["results"], str(mv_grid_id)
    )

    setup_logger(
        loggers=[
            {"name": "edisgo", "file_level": "debug", "stream_level": "debug"},
        ],
        file_name=f"run_edisgo_{mv_grid_id}.log",
        log_dir=results_dir,
    )
    # use edisgo logger in order to have all logging information for one grid go
    # to the same file
    logger = logging.getLogger("edisgo.external.ego._run_edisgo")
    logging.getLogger('pypsa').setLevel(logging.WARNING)

    try:
        if scenario in ["eGon2035", "eGon100RE"]:
            zip_name = "grid_data_optimisation.zip"
        else:
            zip_name = "grid_data_optimisation_lowflex.zip"
        grid_path = os.path.join(results_dir, zip_name)
        edisgo_grid = import_edisgo_from_files(
            edisgo_path=grid_path,
            import_topology=True,
            import_timeseries=True,
            import_results=False,
            import_electromobility=False,
            import_heat_pump=False,
            import_dsm=False,
            import_overlying_grid=False,
            from_zip_archive=True,
        )
        edisgo_grid.legacy_grids = False

        logger.info("Start task 'grid_reinforcement'.")

        # overwrite configs with new configs
        edisgo_grid._config = Config()

        # Add new lines to equipment changes
        grid_path = os.path.join(
            config["eDisGo"]["grid_path"],
            str(mv_grid_id),
        )
        edisgo_grid_orig = import_edisgo_from_files(edisgo_path=grid_path)
        new_lines = [_ for _ in edisgo_grid.topology.lines_df.index if
                     _ not in edisgo_grid_orig.topology.lines_df.index]
        for line_name in new_lines:
            edisgo_grid.results._add_line_to_equipment_changes(
                line=edisgo_grid.topology.lines_df.loc[line_name],
            )

        logger.info("Run grid reinforcement (without n-1).")

        # change configs
        edisgo_grid.config["grid_expansion_load_factors"][
            "mv_load_case_transformer"] = 1.0
        edisgo_grid.config["grid_expansion_load_factors"][
            "mv_load_case_line"] = 1.0

        edisgo_grid = enhanced_reinforce_grid(
            edisgo_grid,
            activate_cost_results_disturbing_mode=True,
            separate_lv_grids=True,
            separation_threshold=2,
            max_while_iterations=30,
        )

        logger.info("Run n-1 grid reinforcement.")

        # set feed-in to zero
        gens_active_power = edisgo_grid.timeseries.generators_active_power.copy()
        gens_reactive_power = edisgo_grid.timeseries.generators_reactive_power.copy()
        gens_ts_new = pd.DataFrame(
            columns=gens_active_power.columns,
            index=gens_active_power.index,
            data=0.0
        )
        edisgo_grid.timeseries.generators_active_power = gens_ts_new
        edisgo_grid.timeseries.generators_reactive_power = gens_ts_new

        # change configs
        edisgo_grid.config["grid_expansion_load_factors"][
            "mv_load_case_transformer"] = 0.5
        edisgo_grid.config["grid_expansion_load_factors"][
            "mv_load_case_line"] = 0.5

        # run MV grid reinforcement (only needed for n-1, as it does not apply in LV)
        catch_convergence_reinforce_grid(edisgo=edisgo_grid, mode="mv")

        # reset feed-in timeseries
        edisgo_grid.timeseries.generators_active_power = gens_active_power
        edisgo_grid.timeseries.generators_reactive_power = gens_reactive_power
        edisgo_grid.save(
            directory=os.path.join(
                results_dir, f"grid_data_reinforcement_{scenario}"
            ),
            save_topology=True,
            save_timeseries=True,
            save_results=True,
            save_electromobility=False,
            save_dsm=False,
            save_heatpump=False,
            save_overlying_grid=False,
            reduce_memory=True,
            archive=True,
            archive_type="zip",
        )
    except:
        logger.exception('')


if __name__ == "__main__":
    jsonpath = os.path.join(os.getcwd(), "scenario_setting_eGon2035.json")
    config = get_scenario_setting(jsonpath=jsonpath)
    scenario = "eGon2035"
    grids = [
        33128, 34186, 31181, 32971, 33111, 31972,
        31133, 32831, 31105, 31180, 31358, 33680,
        34325, 31636, 36029, 36091, 32572, 31140,
        31760, 35920, 31498, 32639, 32829, 32393,
        36023, 32022, 31994, 32101, 32349, 32567,
        35810, 36007, 30977, 33832, 31114, 33577,
        32418, 35958, 35848, 36008, 33105, 32346, 32415
    ]

    for mv_grid in grids:
        #run_edisgo_task_setup_grid(mv_grid, config, scenario)
        #run_edisgo_task_specs_overlying_grid(mv_grid, config, scenario)
        run_temporal_complexity_reduction_new(mv_grid, config)
        #run_edisgo_task_optimisation(mv_grid, config, scenario)
        #run_edisgo_task_grid_reinforcement(mv_grid, config, scenario)
