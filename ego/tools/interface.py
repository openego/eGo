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
This files contains all eGo interface functions
"""

__copyright__ = "Europa-Universität Flensburg, " "Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc,mltja"

import math

# Import
# General Packages
import os
import time

import pandas as pd

if not "READTHEDOCS" in os.environ:
    from egoio.db_tables import model_draft
    from egoio.db_tables import supply

import logging

logger = logging.getLogger(__name__)


class ETraGoMinimalData:
    """
    Container for minimal eTraGo network.

    This minimal network only contains information relevant for eDisGo.

    Parameters
    ----------
    etrago_network : :pypsa:`PyPSA.Network<network>`

    """

    def __init__(self, etrago_network):
        def set_filtered_attribute(etrago_network_obj, component):

            # filter components
            columns_to_save = {
                "links": ["bus0", "bus1", "carrier", "p_nom", "p_nom_opt"],
                "generators": ["bus", "carrier", "p_nom", "p_nom_opt"],
                "stores": ["bus", "carrier", "e_nom", "e_nom_opt"],
                "storage_units": [
                    "bus",
                    "carrier",
                    "p_nom_opt",
                    "p_nom_extendable",
                    "max_hours",
                ],
                "loads": ["bus", "p_set"],
            }
            columns_to_save = columns_to_save[component]

            df = getattr(etrago_network_obj, component)

            logger.info(
                f"Component: {component} has unique carriers: {df.carrier.unique()}"
            )

            setattr(self, component, df[columns_to_save])

            # filter components timeseries
            attribute_to_save = {
                "links": ["p0", "p1"],
                "generators": ["p", "p_max_pu", "q"],
                "stores": ["p"],
                "storage_units": ["p", "q"],
                "loads": ["p"],
            }
            attribute_to_save = attribute_to_save[component]

            component_timeseries_dict = getattr(etrago_network_obj, component + "_t")

            new_component_timeseries_dict = {
                attribute: component_timeseries_dict[attribute]
                for attribute in attribute_to_save
            }

            setattr(self, component + "_t", new_component_timeseries_dict)

        t_start = time.perf_counter()

        self.snapshots = etrago_network.snapshots

        components = ["storage_units", "stores", "generators", "links", "loads"]
        for component in components:
            set_filtered_attribute(etrago_network, component)

        logger.info(f"Data selection time {time.perf_counter()-t_start}")


# Functions
def get_weather_id_for_generator(grid_version, session, generator_index, scn_name):
    # ToDo: Refactor function
    if grid_version is None:
        logger.warning("Weather_id taken from model_draft (not tested)")

        ormclass_gen_single = model_draft.__getattribute__("EgoSupplyPfGeneratorSingle")

        weather_id = (
            session.query(ormclass_gen_single.w_id)
            .filter(
                ormclass_gen_single.aggr_id == generator_index,
                ormclass_gen_single.scn_name == scn_name,
            )
            .limit(1)
            .scalar()
        )

    else:
        ormclass_aggr_w = supply.__getattribute__("EgoAggrWeather")

        weather_id = (
            session.query(ormclass_aggr_w.w_id)
            .filter(
                ormclass_aggr_w.aggr_id == generator_index,
                # ormclass_aggr_w.scn_name == scn_name,
                ormclass_aggr_w.version == grid_version,
            )
            .limit(1)
            .scalar()
        )

    return weather_id


def get_etrago_results_per_bus(
    session,
    bus_id,
    etrago_network,
    grid_version,
    scn_name,
    pf_post_lopf,
    max_cos_phi_renewable,
):
    """
    Reads eTraGo Results from Database and returns
    the interface values as a dictionary of corresponding dataframes

    Parameters
    ----------
    session : sqlalchemy.orm.session.Session
        Handles conversations with the database.
    bus_id : int
        ID of the corresponding HV bus
    etrago_network: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    scn_name : str
        Name of used scenario 'Status Quo', 'NEP 2035' or 'eGo 100'
    pf_post_lopf : bool
        Variable if pf after lopf was run.
    max_cos_phi_renewable : float or None
        If not None, the maximum reactive power is set by the given power factor
        according to the dispatched active power.

    Returns
    -------
    :obj:`dict` of :pandas:`pandas.DataFrame<dataframe>`
        Dataframes used as eDisGo inputs.

        * 'timeindex'
            Timeindex of the etrago-object.
            Type: pd.Datetimeindex

        * 'dispatchable_generators_active_power'
            Normalised dispatch of active power of dispatchable generators per
            technology in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'dispatchable_generators_reactive_power'
            Normalised dispatch of reactive power of dispatchable generators per
            technology in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'renewables_potential'
            Normalised weather dependent feed-in potential of fluctuating generators
            per technology and weather cell ID in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier / Weather Cell ID
            Unit: pu

        * 'renewables_curtailment'
            Normalised curtailment of fluctuating generators per
            technology and weather cell ID in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier / Weather Cell ID
            Unit: pu

        * 'renewables_dispatch_reactive_power'
            Normalised reactive power time series of fluctuating generators per
            technology and weather cell ID in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier / Weather Cell ID
            Unit: pu

        * 'storage_units_capacity'
            Storage unit capacity at the given bus.
            Type: float
            Unit: MWh

        * 'storage_units_active_power'
            Active power time series of battery storage units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'storage_units_reactive_power'
            Reactive power time series of battery storage units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MVar

        * 'dsm_active_power'
            Active power time series of DSM units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'dsm_reactive_power'
            Reactive power time series of DSM units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MVar

        * 'heat_central_active_power'
            Active power time series of central heat units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'heat_central_reactive_power'
            Reactive power time series of central heat units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MVar

        * 'thermal_storage_central_capacity'
            Capacity of the storage at the bus where the central heat units feed in.
            Type: float
            Unit: MWh

        * 'geothermal_energy_feedin_district_heating'
            Geothermal feedin time series at the heat bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'solarthermal_energy_feedin_district_heating'
            Solarthermal feedin time series at the heat bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'heat_pump_rural_active_power'
            Active power time series of rural heat pump units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'heat_pump_rural_reactive_power'
            Reactive power time series of rural heat pump units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MVar

        * 'thermal_storage_rural_capacity'
            Capacity of the storage at the bus where the rural heat units feed in.
            Type: float
            Unit: MWh

        * 'electromobility_active_power'
            Active power time series of electromobility units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'electromobility_reactive_power'
            Reactive power time series of electromobility units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MVar

    """
    performance = {}
    t0 = time.perf_counter()

    logger.info("Specs for bus {}".format(bus_id))
    if pf_post_lopf:
        logger.info("Active and reactive power interface")
    else:
        logger.info("Only active power interface")

    etrago_results_per_bus = {}
    timeseries_index = etrago_network.snapshots
    etrago_results_per_bus["timeindex"] = timeseries_index
    # Prefill dict with None
    result_keys = [
        "dispatchable_generators_active_power",
        "dispatchable_generators_reactive_power",
        "renewables_potential",
        "renewables_curtailment",
        "renewables_dispatch_reactive_power",
        "storage_units_capacity",
        "storage_units_active_power",
        "storage_units_reactive_power",
        "dsm_active_power",
        "dsm_reactive_power",
        "heat_central_active_power",
        "heat_central_reactive_power",
        "thermal_storage_central_capacity",
        "geothermal_energy_feedin_district_heating",
        "solarthermal_energy_feedin_district_heating",
        "heat_pump_rural_active_power",
        "heat_pump_rural_reactive_power",
        "thermal_storage_rural_capacity",
        "electromobility_active_power",
        "electromobility_reactive_power",
    ]
    for key in result_keys:
        etrago_results_per_bus[key] = None

    # Filter dataframes
    # Generators
    generators_df = etrago_network.generators[
        etrago_network.generators["bus"] == str(bus_id)
    ]
    # Links
    links_df = etrago_network.links[
        (etrago_network.links["bus0"] == str(bus_id))
        | (etrago_network.links["bus1"] == str(bus_id))
    ]
    t1 = time.perf_counter()
    performance.update({"General Data Processing": t1 - t0})

    # Dispatchable generators
    dispatchable_generators_df_p = pd.DataFrame(index=timeseries_index)
    if pf_post_lopf:
        dispatchable_generators_df_q = pd.DataFrame(index=timeseries_index)

    dispatchable_generators = [
        "biomass",
        "central_biomass_CHP",
        "industrial_biomass_CHP",
        "run_of_river",
        "gas",
        "other_non_renewable",
        "reservoir",
        "oil",
        "other_renewable",
        "coal",
        "nuclear",
        "lignite",
        "CH4",
        "central_biomass_CHP_heat",
    ]
    dispatchable_generators_df = generators_df[
        generators_df["carrier"].isin(dispatchable_generators)
    ]
    if not dispatchable_generators_df.empty:
        # technology_dict = {
        #     "biomass": ["biomass", "central_biomass_CHP"],
        #     "run_of_river": ["run_of_river"],
        #     "gas": ["gas"],
        #     "other_non_renewable": ["other_non_renewable"],
        #     "reservoir": ["reservoir"],
        # }
        # for key, item in technology_dict.items():
        #     for carrier in item:
        #         dispatchable_generators_df.loc[dispatchable_generators_df["carrier"] == carrier, "carrier"] = key

        for carrier in dispatchable_generators_df["carrier"].unique():
            p_nom = dispatchable_generators_df.loc[
                dispatchable_generators_df["carrier"] == carrier, "p_nom"
            ].sum()
            columns_to_aggregate = dispatchable_generators_df[
                dispatchable_generators_df["carrier"] == carrier
            ].index

            dispatchable_generators_df_p[carrier] = (
                etrago_network.generators_t["p"][columns_to_aggregate].sum(
                    axis="columns"
                )
                / p_nom
            )
            if pf_post_lopf:
                dispatchable_generators_df_q[carrier] = (
                    etrago_network.generators_t["q"][columns_to_aggregate].sum(
                        axis="columns"
                    )
                    / p_nom
                )

    # Add CHP to conventional generators
    chp_df = links_df[links_df["carrier"] == "central_gas_CHP"]
    if not chp_df.empty:
        p_nom = chp_df["p_nom_opt"].sum()
        dispatchable_generators_df_p["central_gas_CHP"] = (
            etrago_network.links_t["p1"][chp_df.index].sum(axis="columns") / p_nom
        )
        if pf_post_lopf:
            dispatchable_generators_df_q["central_gas_CHP"] = (
                0 * dispatchable_generators_df_p["central_gas_CHP"]
            )

        etrago_results_per_bus[
            "dispatchable_generators_active_power"
        ] = dispatchable_generators_df_p
        if pf_post_lopf:
            etrago_results_per_bus[
                "dispatchable_generators_reactive_power"
            ] = dispatchable_generators_df_q

    t2 = time.perf_counter()
    performance.update({"Dispatchable generators": t2 - t1})

    # Renewables
    weather_dependent_generators = [
        "solar",
        "solar_rooftop",
        "wind_onshore",
    ]
    weather_dependent_generators_df = generators_df[
        generators_df.carrier.isin(weather_dependent_generators)
    ]
    if not weather_dependent_generators_df.empty:
        for generator_index in weather_dependent_generators_df.index:
            weather_id = get_weather_id_for_generator(
                grid_version, session, generator_index, scn_name
            )
            weather_dependent_generators_df.loc[generator_index, "w_id"] = str(
                weather_id
            )

        technology_dict = {
            "solar": ["solar", "solar_rooftop"],
        }
        for key, item in technology_dict.items():
            for carrier in item:
                weather_dependent_generators_df.loc[
                    weather_dependent_generators_df["carrier"] == carrier, "carrier"
                ] = key

        # Aggregation of p_nom
        aggregated_weather_dependent_generators_df = (
            weather_dependent_generators_df.groupby(["carrier", "w_id"])
            .agg({"p_nom": "sum"})
            .reset_index()
        )

        # Dispatch and Curtailment
        weather_dependent_generators_df_potential_p = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=aggregated_weather_dependent_generators_df.index,
        )
        weather_dependent_generators_df_dispatch_p = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=aggregated_weather_dependent_generators_df.index,
        )
        if pf_post_lopf:
            weather_dependent_generators_df_dispatch_q = pd.DataFrame(
                0.0,
                index=timeseries_index,
                columns=aggregated_weather_dependent_generators_df.index,
            )

        for index, carrier, w_id, p_nom in weather_dependent_generators_df[
            ["carrier", "w_id", "p_nom"]
        ].itertuples():
            aggregated_idx = aggregated_weather_dependent_generators_df[
                (aggregated_weather_dependent_generators_df["carrier"] == carrier)
                & (aggregated_weather_dependent_generators_df["w_id"] == w_id)
            ].index.values[0]
            p_nom_aggregated = aggregated_weather_dependent_generators_df.loc[
                aggregated_idx, "p_nom"
            ]

            p_series = etrago_network.generators_t["p"][index]
            p_normed_series = p_series / p_nom_aggregated

            p_max_pu_series = etrago_network.generators_t["p_max_pu"][index]
            p_max_pu_normed_series = p_max_pu_series * p_nom / p_nom_aggregated

            if pf_post_lopf:
                if max_cos_phi_renewable:
                    logger.info(
                        "Applying Q limit (max cos(phi)={})".format(
                            max_cos_phi_renewable
                        )
                    )

                    phi = math.acos(max_cos_phi_renewable)

                    q_series = pd.Series(0, index=timeseries_index)

                    for timestep in timeseries_index:
                        p = etrago_network.generators_t["p"].loc[timestep, index]
                        q = etrago_network.generators_t["q"].loc[timestep, index]

                        q_max = p * math.tan(phi)
                        q_min = -p * math.tan(phi)

                        if q > q_max:
                            q = q_max
                        elif q < q_min:
                            q = q_min

                        q_series[timestep] = q
                else:
                    q_series = etrago_network.generators_t["q"][index]

                q_normed_series = q_series / p_nom_aggregated

            weather_dependent_generators_df_dispatch_p[aggregated_idx] = (
                weather_dependent_generators_df_dispatch_p[aggregated_idx]
                + p_normed_series
            )
            weather_dependent_generators_df_potential_p[aggregated_idx] = (
                weather_dependent_generators_df_potential_p[aggregated_idx]
                + p_max_pu_normed_series
            )
            if pf_post_lopf:
                weather_dependent_generators_df_dispatch_q[aggregated_idx] = (
                    weather_dependent_generators_df_dispatch_q[aggregated_idx]
                    + q_normed_series
                )

        weather_dependent_generators_df_curtailment_p = (
            weather_dependent_generators_df_potential_p
            - weather_dependent_generators_df_dispatch_p
        )

        # Renaming columns
        new_columns = [
            (
                aggregated_weather_dependent_generators_df.at[column, "carrier"],
                aggregated_weather_dependent_generators_df.at[column, "w_id"],
            )
            for column in weather_dependent_generators_df_potential_p.columns
        ]
        new_columns = pd.MultiIndex.from_tuples(new_columns)
        weather_dependent_generators_df_potential_p.columns = new_columns
        weather_dependent_generators_df_dispatch_p.columns = new_columns
        weather_dependent_generators_df_curtailment_p.columns = new_columns
        if pf_post_lopf:
            weather_dependent_generators_df_dispatch_q.columns = new_columns

        etrago_results_per_bus[
            "renewables_potential"
        ] = weather_dependent_generators_df_potential_p
        etrago_results_per_bus[
            "renewables_curtailment"
        ] = weather_dependent_generators_df_curtailment_p
        if pf_post_lopf:
            etrago_results_per_bus[
                "renewables_dispatch_reactive_power"
            ] = weather_dependent_generators_df_dispatch_q

    t3 = time.perf_counter()
    performance.update({"Renewable Dispatch and Curt.": t3 - t2})

    # Storage
    # Filter batteries
    min_extended = 0
    logger.info(f"Minimum storage of {min_extended} MW")

    storages_df = etrago_network.storage_units.loc[
        (etrago_network.storage_units["carrier"] == "battery")
        & (etrago_network.storage_units["bus"] == str(bus_id))
        & (etrago_network.storage_units["p_nom_extendable"] == True)
        & (etrago_network.storage_units["p_nom_opt"] > min_extended)
        # & (etrago_network.storage_units["max_hours"] <= 20.0)
    ]
    if not storages_df.empty:
        # Capactiy
        storages_df_capacity = (
            storages_df["p_nom_opt"] * storages_df["max_hours"]
        ).values[0]

        storages_df_p = etrago_network.storage_units_t["p"][storages_df.index]
        storages_df_p.columns = storages_df["carrier"]
        if pf_post_lopf:
            storages_df_q = etrago_network.storage_units_t["q"][storages_df.index]
            storages_df_q.columns = storages_df["carrier"]

        etrago_results_per_bus["storage_units_capacity"] = storages_df_capacity
        etrago_results_per_bus["storage_units_active_power"] = storages_df_p
        if pf_post_lopf:
            etrago_results_per_bus["storage_units_reactive_power"] = storages_df_q

    t4 = time.perf_counter()
    performance.update({"Storage Data Processing": t4 - t3})

    # DSM
    dsm_df = links_df.loc[
        (links_df["carrier"] == "dsm") & (links_df["bus0"] == str(bus_id))
    ]
    if not dsm_df.empty:
        if dsm_df.shape[0] > 1:
            raise ValueError(f"More than one dsm link at bus {bus_id}")
        dsm_df_p = etrago_network.links_t["p0"][dsm_df.index]
        dsm_df_p.columns = dsm_df["carrier"]
        if pf_post_lopf:
            dsm_df_q = 0 * dsm_df_p

        etrago_results_per_bus["dsm_active_power"] = dsm_df_p
        if pf_post_lopf:
            etrago_results_per_bus["dsm_reactive_power"] = dsm_df_q

    t5 = time.perf_counter()
    performance.update({"DSM Data Processing": t5 - t4})

    # Heat
    # Central heat
    # Power2Heat
    central_heat_carriers = ["central_heat_pump", "central_resistive_heater"]
    central_heat_df = links_df.loc[
        links_df["carrier"].isin(central_heat_carriers)
        & (links_df["bus0"] == str(bus_id))
    ]
    if not central_heat_df.empty:
        # Timeseries
        central_heat_df_p = etrago_network.links_t["p0"][central_heat_df.index]
        central_heat_df_p.columns = central_heat_df["carrier"]
        if pf_post_lopf:
            central_heat_df_q = 0 * central_heat_df_p

        etrago_results_per_bus["heat_central_active_power"] = central_heat_df_p
        if pf_post_lopf:
            etrago_results_per_bus["heat_central_reactive_power"] = central_heat_df_q

        # Stores
        central_heat_bus = central_heat_df["bus1"].values[0]
        central_heat_store_bus = etrago_network.links.loc[
            etrago_network.links["bus0"] == central_heat_bus, "bus1"
        ].values[0]
        central_heat_store_capacity = etrago_network.stores.loc[
            (etrago_network.stores["carrier"] == "central_heat_store")
            & (etrago_network.stores["bus"] == central_heat_store_bus),
            "e_nom_opt",
        ].values[0]

        etrago_results_per_bus[
            "thermal_storage_central_capacity"
        ] = central_heat_store_capacity

        # Feedin
        geothermal_feedin_df = etrago_network.generators[
            (etrago_network.generators["carrier"] == "geo_thermal")
            & (etrago_network.generators["bus"] == central_heat_bus)
        ]
        geothermal_feedin_df_p = etrago_network.generators_t["p"][
            geothermal_feedin_df.index
        ]
        geothermal_feedin_df_p.columns = geothermal_feedin_df["carrier"]
        etrago_results_per_bus[
            "geothermal_energy_feedin_district_heating"
        ] = geothermal_feedin_df_p

        solarthermal_feedin_df = etrago_network.generators[
            (etrago_network.generators["carrier"] == "solar_thermal_collector")
            & (etrago_network.generators["bus"] == central_heat_bus)
        ]
        solarthermal_feedin_df_p = etrago_network.generators_t["p"][
            solarthermal_feedin_df.index
        ]
        solarthermal_feedin_df_p.columns = solarthermal_feedin_df["carrier"]
        etrago_results_per_bus[
            "solarthermal_energy_feedin_district_heating"
        ] = solarthermal_feedin_df_p

    t6 = time.perf_counter()
    performance.update({"Central Heat Data Processing": t6 - t5})

    # Rural heat
    # Power2Heat
    rural_heat_carriers = ["rural_heat_pump"]
    rural_heat_df = links_df.loc[
        links_df["carrier"].isin(rural_heat_carriers)
        & (links_df["bus0"] == str(bus_id))
    ]
    if not rural_heat_df.empty:
        # Timeseries
        rural_heat_df_p = etrago_network.links_t["p0"][rural_heat_df.index]
        rural_heat_df_p.columns = rural_heat_df["carrier"]
        if pf_post_lopf:
            rural_heat_df_q = 0 * rural_heat_df_p

        etrago_results_per_bus["heat_pump_rural_active_power"] = rural_heat_df_p
        if pf_post_lopf:
            etrago_results_per_bus["heat_pump_rural_reactive_power"] = rural_heat_df_q

        # Stores
        rural_heat_bus = rural_heat_df["bus1"].values[0]
        rural_heat_store_bus = etrago_network.links.loc[
            etrago_network.links["bus0"] == rural_heat_bus, "bus1"
        ].values[0]
        rural_heat_store_capacity = etrago_network.stores.loc[
            (etrago_network.stores["carrier"] == "rural_heat_store")
            & (etrago_network.stores["bus"] == rural_heat_store_bus),
            "e_nom_opt",
        ].values[0]

        etrago_results_per_bus[
            "thermal_storage_rural_capacity"
        ] = rural_heat_store_capacity

    t7 = time.perf_counter()
    performance.update({"Rural Heat Data Processing": t7 - t6})

    # BEV charger
    bev_charger_df = links_df.loc[
        (links_df["carrier"] == "BEV charger") & (links_df["bus0"] == str(bus_id))
    ]
    if not bev_charger_df.empty:
        if bev_charger_df.shape[0] > 1:
            raise ValueError(f"More than one dsm link at bus {bus_id}")

        bev_charger_df_p = etrago_network.links_t["p0"][bev_charger_df.index]
        bev_charger_df_p.columns = bev_charger_df["carrier"]
        if pf_post_lopf:
            bev_charger_df_q = 0 * bev_charger_df_p

        etrago_results_per_bus["electromobility_active_power"] = bev_charger_df_p
        if pf_post_lopf:
            etrago_results_per_bus["electromobility_reactive_power"] = bev_charger_df_q

    t8 = time.perf_counter()
    performance.update({"BEV Data Processing": t8 - t7})
    performance.update({"Overall time": t8 - t0})
    logger.info(performance)

    return etrago_results_per_bus
