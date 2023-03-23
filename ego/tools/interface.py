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

import logging
import math
import time

import pandas as pd

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
                    "p_nom_min",
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
                "storage_units": ["p", "q", "state_of_charge"],
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
        for selected_component in components:
            set_filtered_attribute(etrago_network, selected_component)

        logger.info(f"Data selection time {time.perf_counter() - t_start}")


def get_etrago_results_per_bus(bus_id, etrago_obj, pf_post_lopf, max_cos_phi_ren):
    """
    Reads eTraGo Results from Database and returns
    the interface values as a dictionary of corresponding dataframes

    Parameters
    ----------
    engine:
        Engine of the database.
    orm:
        Object relational model dict.
    bus_id : int
        ID of the corresponding HV bus
    etrago_obj: :class:`etrago.tools.io.NetworkScenario`
        eTraGo network object compiled by :meth:`etrago.appl.etrago`
    pf_post_lopf : bool
        Variable if pf after lopf was run.
    max_cos_phi_ren : float or None
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
            per technology in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'renewables_curtailment'
            Normalised curtailment of fluctuating generators per
            technology in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'renewables_dispatch_reactive_power'
            Normalised reactive power time series of fluctuating generators per
            technology in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'storage_units_p_nom'
            Storage unit nominal power.
            Type: float
            Unit: MW

        * 'storage_units_max_hours'
            Storage units maximal discharge with p_nom starting by a soc of 1.
            Type: float
            Unit: h

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

        * 'storage_units_soc'
            Reactive power time series of battery storage units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

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

        * 'heat_pump_central_active_power'
            Active power time series of central heat units at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'heat_pump_central_reactive_power'
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
    # Defining inner functions

    def dispatchable_gens():
        # Dispatchable generators
        dispatchable_gens_df_p = pd.DataFrame(index=timeseries_index)
        dispatchable_gens_df_q = pd.DataFrame(index=timeseries_index)

        dispatchable_gens_carriers = [
            # "CH4",
            # "CH4_NG",
            # "CH4_biogas",
            "biomass",
            "central_biomass_CHP",
            # "central_biomass_CHP_heat",
            # "coal",
            # "geo_thermal",
            "industrial_biomass_CHP",
            # "lignite",
            # "nuclear",
            # "oil",
            "others",
            "reservoir",
            "run_of_river",
            # "solar",
            # "solar_rooftop",
            # "solar_thermal_collector",
            # "wind_offshore",
            # "wind_onshore",
        ]
        # Filter generators_df for selected carriers.
        dispatchable_gens_df = generators_df[
            generators_df["carrier"].isin(dispatchable_gens_carriers)
        ]
        for carrier in dispatchable_gens_carriers:
            if not dispatchable_gens_df[
                dispatchable_gens_df["carrier"] == carrier
            ].empty:
                p_nom = dispatchable_gens_df.loc[
                    dispatchable_gens_df["carrier"] == carrier, "p_nom"
                ].sum()
                columns_to_aggregate = dispatchable_gens_df[
                    dispatchable_gens_df["carrier"] == carrier
                ].index

                dispatchable_gens_df_p[carrier] = (
                    etrago_obj.generators_t["p"][columns_to_aggregate].sum(
                        axis="columns"
                    )
                    / p_nom
                )
                if pf_post_lopf:
                    dispatchable_gens_df_q[carrier] = (
                        etrago_obj.generators_t["q"][columns_to_aggregate].sum(
                            axis="columns"
                        )
                        / p_nom
                    )
                else:
                    dispatchable_gens_df_q[carrier] = pd.Series(
                        data=0, index=timeseries_index, dtype=float
                    )
            else:
                dispatchable_gens_df_p[carrier] = pd.Series(
                    data=0, index=timeseries_index, dtype=float
                )
                dispatchable_gens_df_q[carrier] = pd.Series(
                    data=0, index=timeseries_index, dtype=float
                )

        # Add CHP to conventional generators
        if pf_post_lopf:
            chp_df = generators_df[generators_df["carrier"] == "central_gas_CHP"]
        else:
            chp_df = links_df[links_df["carrier"] == "central_gas_CHP"]
        if not chp_df.empty:
            p_nom = chp_df["p_nom"].sum()
            if pf_post_lopf:
                dispatchable_gens_df_p["central_gas_CHP"] = (
                    etrago_obj.generators_t["p"][chp_df.index].sum(axis="columns")
                    / p_nom
                )
                dispatchable_gens_df_q["central_gas_CHP"] = (
                    etrago_obj.generators_t["q"][chp_df.index].sum(axis="columns")
                    / p_nom
                )
            else:
                dispatchable_gens_df_p["central_gas_CHP"] = (
                    etrago_obj.links_t["p1"][chp_df.index].sum(axis="columns") / p_nom
                )
                dispatchable_gens_df_q["central_gas_CHP"] = pd.Series(
                    data=0, index=timeseries_index, dtype=float
                )
        else:
            dispatchable_gens_df_p["central_gas_CHP"] = pd.Series(
                data=0, index=timeseries_index, dtype=float
            )
            dispatchable_gens_df_q["central_gas_CHP"] = pd.Series(
                data=0, index=timeseries_index, dtype=float
            )

        results["dispatchable_generators_active_power"] = dispatchable_gens_df_p
        results["dispatchable_generators_reactive_power"] = dispatchable_gens_df_q

    def renewable_generators():
        """
        # Renewables
        weather_dependent = weather_dep
        generators = gens
        weather_id = w_id
        aggregated = agg
        potential = pot
        dispatch = dis
        curtailment = curt
        """

        weather_dep_gens = [
            # "CH4",
            # "CH4_NG",
            # "CH4_biogas",
            # "biomass",
            # "central_biomass_CHP",
            # "central_biomass_CHP_heat",
            # "coal",
            # "geo_thermal",
            # "industrial_biomass_CHP",
            # "lignite",
            # "nuclear",
            # "oil",
            # "others",
            # "reservoir",
            # "run_of_river",
            "solar",
            "solar_rooftop",
            # "solar_thermal_collector",
            # "wind_offshore",
            "wind_onshore",
        ]
        renaming_carrier_dict = {
            "solar": ["solar", "solar_rooftop"],
            "wind": ["wind_onshore"],
        }
        weather_dep_gens_df = generators_df[
            generators_df.carrier.isin(weather_dep_gens)
        ]

        # ToDo @Malte please check
        # # Add weather ids
        # for gens_index in weather_dep_gens_df.index:
        #     weather_id = db_io.get_weather_id_for_generator(
        #         bus_id, engine=engine, orm=orm
        #     )
        #     weather_dep_gens_df.loc[gens_index, "w_id"] = str(weather_id)

        # Rename carrier to aggregate to carriers
        for new_carrier_name, item in renaming_carrier_dict.items():
            for carrier in item:
                weather_dep_gens_df.loc[
                    weather_dep_gens_df["carrier"] == carrier, "carrier"
                ] = new_carrier_name

        # Aggregation of p_nom
        agg_weather_dep_gens_df = (
            weather_dep_gens_df.groupby(["carrier"]).agg({"p_nom": "sum"}).reset_index()
        )

        # Initialize dfs
        weather_dep_gens_df_pot_p = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=agg_weather_dep_gens_df.index,
        )
        weather_dep_gens_df_dis_p = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=agg_weather_dep_gens_df.index,
        )
        weather_dep_gens_df_dis_q = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=agg_weather_dep_gens_df.index,
        )
        weather_dep_gens_df_curt_p = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=agg_weather_dep_gens_df.index,
        )

        for index, carrier, p_nom in weather_dep_gens_df[
            ["carrier", "p_nom"]
        ].itertuples():
            agg_idx = agg_weather_dep_gens_df[
                agg_weather_dep_gens_df["carrier"] == carrier
            ].index.values[0]
            p_nom_agg = agg_weather_dep_gens_df.loc[agg_idx, "p_nom"]

            p_series = etrago_obj.generators_t["p"][index]
            p_normed_series = p_series / p_nom_agg

            p_max_pu_series = etrago_obj.generators_t["p_max_pu"][index]
            p_max_pu_normed_series = p_max_pu_series * p_nom / p_nom_agg

            if pf_post_lopf:
                q_series = etrago_obj.generators_t["q"][index]
            else:
                q_series = pd.Series(0.0, index=timeseries_index)

            # If set limit maximum reactive power
            if max_cos_phi_ren:
                logger.info(
                    "Applying Q limit (max cos(phi)={})".format(max_cos_phi_ren)
                )
                phi = math.acos(max_cos_phi_ren)
                for timestep in timeseries_index:
                    p = p_series[timestep]
                    q = q_series[timestep]
                    q_max = p * math.tan(phi)
                    q_min = -p * math.tan(phi)
                    if q > q_max:
                        q = q_max
                    elif q < q_min:
                        q = q_min
                    q_series[timestep] = q

            q_normed_series = q_series / p_nom_agg

            weather_dep_gens_df_dis_p[agg_idx] = (
                weather_dep_gens_df_dis_p[agg_idx] + p_normed_series
            )
            weather_dep_gens_df_pot_p[agg_idx] = (
                weather_dep_gens_df_pot_p[agg_idx] + p_max_pu_normed_series
            )
            weather_dep_gens_df_dis_q[agg_idx] = (
                weather_dep_gens_df_dis_q[agg_idx] + q_normed_series
            )
            weather_dep_gens_df_curt_p[agg_idx] = weather_dep_gens_df_curt_p[
                agg_idx
            ] + (p_max_pu_series * p_nom - p_series)

        # Renaming columns
        new_columns = [
            (agg_weather_dep_gens_df.at[column, "carrier"])
            for column in weather_dep_gens_df_pot_p.columns
        ]
        # new_columns = pd.MultiIndex.from_tuples(new_columns)
        weather_dep_gens_df_pot_p.columns = new_columns
        weather_dep_gens_df_dis_p.columns = new_columns
        weather_dep_gens_df_curt_p.columns = new_columns
        weather_dep_gens_df_dis_q.columns = new_columns

        # Add zero for empty carriers
        for carrier in renaming_carrier_dict.keys():
            if carrier not in weather_dep_gens_df_pot_p.columns:
                empty_df = pd.DataFrame(
                    0.0,
                    index=timeseries_index,
                    columns=[carrier],
                )
                weather_dep_gens_df_pot_p = pd.concat(
                    [weather_dep_gens_df_pot_p, empty_df.copy()], axis="columns"
                )
                weather_dep_gens_df_dis_p = pd.concat(
                    [weather_dep_gens_df_dis_p, empty_df.copy()], axis="columns"
                )
                weather_dep_gens_df_curt_p = pd.concat(
                    [weather_dep_gens_df_curt_p, empty_df.copy()], axis="columns"
                )
                weather_dep_gens_df_dis_q = pd.concat(
                    [weather_dep_gens_df_dis_q, empty_df.copy()], axis="columns"
                )

        results["renewables_potential"] = weather_dep_gens_df_pot_p
        results["renewables_curtailment"] = weather_dep_gens_df_curt_p
        results["renewables_dispatch_reactive_power"] = weather_dep_gens_df_dis_q

    def storages():
        # Storage
        # Filter batteries
        min_extended = 0
        logger.info(f"Minimum storage of {min_extended} MW")

        storages_df = etrago_obj.storage_units.loc[
            (etrago_obj.storage_units["carrier"] == "battery")
            & (etrago_obj.storage_units["bus"] == str(bus_id))
            & (etrago_obj.storage_units["p_nom_extendable"])
            & (etrago_obj.storage_units["p_nom_opt"] > min_extended)
        ]
        if not storages_df.empty:
            # p_nom
            storages_df_p_nom = (
                storages_df["p_nom_opt"] - storages_df["p_nom_min"]
            ).values[0]
            # Capacity
            storages_df_max_hours = (storages_df["max_hours"]).values[0]
            storages_df_p = etrago_obj.storage_units_t["p"][storages_df.index]
            storages_df_p.columns = storages_df["carrier"]
            if pf_post_lopf:
                # ToDo: No q timeseries?
                # storages_df_q = etrago_obj.storage_units_t["q"][storages_df.index]
                # storages_df_q.columns = storages_df["carrier"]
                storages_df_q = pd.DataFrame(
                    0.0, index=timeseries_index, columns=[storages_df["carrier"]]
                )
            else:
                storages_df_q = pd.DataFrame(
                    0.0, index=timeseries_index, columns=[storages_df["carrier"]]
                )
            storages_df_soc = etrago_obj.storage_units_t["state_of_charge"][
                storages_df.index
            ]
            storages_df_soc.columns = storages_df["carrier"]

        else:
            storages_df_p_nom = 0
            storages_df_max_hours = 0
            storages_df_p = pd.DataFrame(
                0.0, index=timeseries_index, columns=[storages_df["carrier"]]
            )
            storages_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=[storages_df["carrier"]]
            )
            storages_df_soc = pd.DataFrame(
                0.0, index=timeseries_index, columns=[storages_df["carrier"]]
            )
        results["storage_units_p_nom"] = storages_df_p_nom
        results["storage_units_max_hours"] = storages_df_max_hours
        results["storage_units_active_power"] = storages_df_p
        results["storage_units_reactive_power"] = storages_df_q
        results["storage_units_soc"] = storages_df_soc

    def dsm():
        # DSM
        dsm_df = links_df.loc[
            (links_df["carrier"] == "dsm") & (links_df["bus0"] == str(bus_id))
        ]
        if not dsm_df.empty:
            dsm_df_p = etrago_obj.links_t["p0"][dsm_df.index]
            dsm_df_p.columns = dsm_df["carrier"]
            dsm_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=[dsm_df["carrier"]]
            )
        else:
            dsm_df_p = pd.DataFrame(
                0.0, index=timeseries_index, columns=[dsm_df["carrier"]]
            )
            dsm_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=[dsm_df["carrier"]]
            )
        results["dsm_active_power"] = dsm_df_p
        results["dsm_reactive_power"] = dsm_df_q

    def central_heat():
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
            central_heat_df_p = etrago_obj.links_t["p0"][central_heat_df.index]
            central_heat_df_p.columns = central_heat_df["carrier"]
            central_heat_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=[central_heat_df["carrier"]]
            )

            # Stores
            central_heat_bus = central_heat_df["bus1"].values[0]
            central_heat_store_bus = etrago_obj.links.loc[
                etrago_obj.links["bus0"] == central_heat_bus, "bus1"
            ].values[0]
            central_heat_store_capacity = etrago_obj.stores.loc[
                (etrago_obj.stores["carrier"] == "central_heat_store")
                & (etrago_obj.stores["bus"] == central_heat_store_bus),
                "e_nom_opt",
            ].values[0]

            # Feedin
            geothermal_feedin_df = etrago_obj.generators[
                (etrago_obj.generators["carrier"] == "geo_thermal")
                & (etrago_obj.generators["bus"] == central_heat_bus)
            ]
            if not geothermal_feedin_df.empty:
                geothermal_feedin_df_p = etrago_obj.generators_t["p"][
                    geothermal_feedin_df.index
                ]
                geothermal_feedin_df_p.columns = geothermal_feedin_df["carrier"]
            else:
                geothermal_feedin_df_p = pd.DataFrame(
                    0.0, index=timeseries_index, columns=["geo_thermal"]
                )

            solarthermal_feedin_df = etrago_obj.generators[
                (etrago_obj.generators["carrier"] == "solar_thermal_collector")
                & (etrago_obj.generators["bus"] == central_heat_bus)
            ]
            if not solarthermal_feedin_df.empty:
                solarthermal_feedin_df_p = etrago_obj.generators_t["p"][
                    solarthermal_feedin_df.index
                ]
                solarthermal_feedin_df_p.columns = solarthermal_feedin_df["carrier"]
            else:
                solarthermal_feedin_df_p = pd.DataFrame(
                    0.0, index=timeseries_index, columns=["solar_thermal_collector"]
                )
        else:
            column_names = central_heat_df["carrier"].to_list()
            central_heat_df_p = pd.DataFrame(
                0.0, index=timeseries_index, columns=column_names
            )
            central_heat_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=column_names
            )
            central_heat_store_capacity = 0
            geothermal_feedin_df_p = pd.DataFrame(
                0.0, index=timeseries_index, columns=["geo_thermal"]
            )
            solarthermal_feedin_df_p = pd.DataFrame(
                0.0, index=timeseries_index, columns=["solar_thermal_collector"]
            )
        # ToDo: Overlying grid no resistive heater
        results["heat_pump_central_active_power"] = central_heat_df_p
        results["heat_pump_central_reactive_power"] = central_heat_df_q
        results["thermal_storage_central_capacity"] = central_heat_store_capacity
        results["geothermal_energy_feedin_district_heating"] = geothermal_feedin_df_p
        results[
            "solarthermal_energy_feedin_district_heating"
        ] = solarthermal_feedin_df_p

    def rural_heat():
        # Rural heat
        # Power2Heat
        rural_heat_carriers = ["rural_heat_pump"]
        rural_heat_df = links_df.loc[
            links_df["carrier"].isin(rural_heat_carriers)
            & (links_df["bus0"] == str(bus_id))
        ]
        if not rural_heat_df.empty:
            # Timeseries
            rural_heat_df_p = etrago_obj.links_t["p0"][rural_heat_df.index]
            rural_heat_df_p.columns = rural_heat_df["carrier"]
            rural_heat_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=[rural_heat_df["carrier"]]
            )

            # Stores
            rural_heat_bus = rural_heat_df["bus1"].values[0]
            rural_heat_store_bus = etrago_obj.links.loc[
                etrago_obj.links["bus0"] == rural_heat_bus, "bus1"
            ].values[0]
            rural_heat_store_capacity = etrago_obj.stores.loc[
                (etrago_obj.stores["carrier"] == "rural_heat_store")
                & (etrago_obj.stores["bus"] == rural_heat_store_bus),
                "e_nom_opt",
            ].values[0]
        else:
            column_names = rural_heat_df["carrier"].to_list()
            rural_heat_df_p = pd.DataFrame(
                0.0, index=timeseries_index, columns=column_names
            )
            rural_heat_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=column_names
            )
            rural_heat_store_capacity = 0

        results["heat_pump_rural_active_power"] = rural_heat_df_p
        results["heat_pump_rural_reactive_power"] = rural_heat_df_q
        results["thermal_storage_rural_capacity"] = rural_heat_store_capacity

    def bev_charger():
        # BEV charger
        bev_charger_df = links_df.loc[
            (links_df["carrier"] == "BEV charger") & (links_df["bus0"] == str(bus_id))
        ]
        if not bev_charger_df.empty:
            bev_charger_df_p = etrago_obj.links_t["p0"][bev_charger_df.index]
            bev_charger_df_p.columns = bev_charger_df["carrier"]
            bev_charger_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=[bev_charger_df["carrier"]]
            )
        else:
            bev_charger_df_p = pd.DataFrame(
                0.0, index=timeseries_index, columns=[bev_charger_df["carrier"]]
            )
            bev_charger_df_q = pd.DataFrame(
                0.0, index=timeseries_index, columns=[bev_charger_df["carrier"]]
            )

        results["electromobility_active_power"] = bev_charger_df_p
        results["electromobility_reactive_power"] = bev_charger_df_q

    # Function part
    t_start = time.perf_counter()

    logger.info("Specs for bus {}".format(bus_id))
    if pf_post_lopf:
        logger.info("Active and reactive power interface")
    else:
        logger.info("Only active power interface")

    results = {}
    timeseries_index = etrago_obj.snapshots
    results["timeindex"] = timeseries_index
    # Prefill dict with None
    result_keys = [
        "timeindex",
        "dispatchable_generators_active_power",
        "dispatchable_generators_reactive_power",
        "renewables_potential",
        "renewables_curtailment",
        "renewables_dispatch_reactive_power",
        "storage_units_p_nom",
        "storage_units_max_hours",
        "storage_units_active_power",
        "storage_units_reactive_power",
        "storage_units_soc",
        "dsm_active_power",
        "dsm_reactive_power",
        "heat_pump_central_active_power",
        "heat_pump_central_reactive_power",
        "thermal_storage_central_capacity",
        "geothermal_energy_feedin_district_heating",
        "solarthermal_energy_feedin_district_heating",
        "heat_pump_rural_active_power",
        "heat_pump_rural_reactive_power",
        "thermal_storage_rural_capacity",
        "electromobility_active_power",
        "electromobility_reactive_power",
    ]
    for result_key in result_keys:
        results[result_key] = None

    # Filter dataframes by bus_id
    # Generators
    generators_df = etrago_obj.generators[etrago_obj.generators["bus"] == str(bus_id)]
    # Links
    links_df = etrago_obj.links[
        (etrago_obj.links["bus0"] == str(bus_id))
        | (etrago_obj.links["bus1"] == str(bus_id))
    ]

    # Fill results
    dispatchable_gens()
    renewable_generators()
    storages()
    dsm()
    central_heat()
    rural_heat()
    bev_charger()
    logger.info(f"Overall time: {time.perf_counter() - t_start}")

    return results
