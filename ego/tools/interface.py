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
                "links": [
                    "bus0",
                    "bus1",
                    "carrier",
                    "p_nom",
                    "p_nom_opt",
                    "efficiency",
                ],
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
                "stores": ["p", "e"],
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
    dict(str: :pandas:`pandas.DataFrame<dataframe>`)
        Dataframes used as eDisGo inputs.

        * 'timeindex'
            Timeindex of the etrago-object.
            Type: pd.Datetimeindex

        * 'dispatchable_generators_active_power'
            Normalised active power dispatch of dispatchable generators per
            technology in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'dispatchable_generators_reactive_power'
            Normalised reactive power dispatch of dispatchable generators per
            technology in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'renewables_potential'
            Normalised weather dependent feed-in potential of fluctuating generators
            per technology (solar / wind) in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'renewables_curtailment'
            Curtailment of fluctuating generators per
            technology (solar / wind) in MW at the given bus. This curtailment can also
            include curtailment of plants at the HV side of the HV/MV station and
            therefore needs to be scaled using the quotient of installed power at the
            MV side and installed power at the HV side.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: MW

        * 'renewables_dispatch_reactive_power'
            Normalised reactive power time series of fluctuating generators per
            technology in p.u. at the given bus.
            Type: pd.DataFrame
            Columns: Carrier
            Unit: pu

        * 'renewables_p_nom'
            Installed capacity of fluctuating generators per
            technology (solar / wind) at the given bus.
            Type: pd.Series with carrier in index
            Unit: MW

        * 'storage_units_p_nom'
            Storage unit nominal power.
            Type: float
            Unit: MW

        * 'storage_units_max_hours'
            Storage units maximal discharge hours when discharged with p_nom starting
            at a SoC of 1.
            Type: float
            Unit: h

        * 'storage_units_active_power'
            Active power time series of battery storage units at the given bus.
            Type: pd.Series
            Unit: MW

        * 'storage_units_reactive_power'
            Reactive power time series of battery storage units at the given bus.
            Type: pd.Series
            Unit: MVar

        * 'storage_units_soc'
            State of charge in p.u. of battery storage units at the given bus.
            Type: pd.Series
            Unit: pu

        * 'dsm_active_power'
            Active power time series of DSM units at the given bus.
            Type: pd.Series
            Unit: MW

        * 'heat_pump_rural_active_power'
            Active power time series of PtH units for individual heating at the given
            bus.
            Type: pd.Series
            Unit: MW

        * 'heat_pump_rural_reactive_power'
            Reactive power time series of PtH units for individual heating at the given
            bus.
            Type: pd.Series
            Unit: MVar

        * 'heat_pump_rural_p_nom'
            Nominal power of all PtH units for individual heating at the given bus.
            Type: float
            Unit: MW

        * 'thermal_storage_rural_capacity'
            Capacity of thermal storage units in individual heating.
            Type: float
            Unit: MWh

        * 'thermal_storage_rural_efficiency'
            Charging and discharging efficiency of thermal storage units in individual
            heating.
            Type: float
            Unit: p.u.

        * 'thermal_storage_rural_soc'
            SoC of central thermal storage units.
            Type: pd.Series
            Unit: p.u.

        * 'heat_pump_central_active_power'
            Active power time series of central PtH units at the given bus.
            Type: pd.Series
            Unit: MW

        * 'heat_pump_central_reactive_power'
            Reactive power time series of central PtH units at the given bus.
            Type: pd.Series
            Unit: MVar

        * 'heat_pump_central_p_nom'
            Nominal power of all central PtH units at the given bus.
            Type: float
            Unit: MW

        * 'thermal_storage_central_capacity'
            Capacity of central thermal storage units.
            Type: pd.Series with eTraGo heat bus ID in index
            Unit: MWh

        * 'thermal_storage_central_efficiency'
            Charging and discharging efficiency of central thermal storage units.
            Type: float
            Unit: p.u.

        * 'thermal_storage_central_soc'
            SoC of central thermal storage units.
            Type: pd.DataFrame
            Columns: eTraGo heat bus ID
            Unit: p.u.

        * 'feedin_district_heating'
            Time series of other thermal feed-in from e.g. gas boilers or geothermal
            units at the heat bus.
            Type: pd.DataFrame
            Columns: eTraGo heat bus ID
            Unit: MW

        * 'electromobility_active_power'
            Active power charging time series at the given bus.
            Type: pd.Series
            Unit: MW

        * 'electromobility_reactive_power'
            Reactive power charging time series at the given bus.
            Type: pd.Series
            Unit: MVar

    """

    def dispatchable_gens():
        dispatchable_gens_df_p = pd.DataFrame(index=timeseries_index)
        dispatchable_gens_df_q = pd.DataFrame(index=timeseries_index)

        dispatchable_gens_carriers = [
            _
            for _ in generators_df["carrier"].unique()
            if "solar" not in _ and "wind" not in _
        ]
        # Filter generators_df for selected carriers.
        dispatchable_gens_df = generators_df[
            generators_df["carrier"].isin(dispatchable_gens_carriers)
        ]
        # Rename carriers to match with carrier names in eDisGo
        gens = dispatchable_gens_df[
            dispatchable_gens_df.carrier.isin(["central_gas_CHP", "industrial_gas_CHP"])
        ]
        dispatchable_gens_df.loc[gens.index, "carrier"] = "gas_CHP"
        gens = dispatchable_gens_df[
            dispatchable_gens_df.carrier.isin(
                ["central_biomass_CHP", "industrial_biomass_CHP"]
            )
        ]
        dispatchable_gens_df.loc[gens.index, "carrier"] = "biomass_CHP"
        gens = dispatchable_gens_df[dispatchable_gens_df.carrier.isin(["reservoir"])]
        dispatchable_gens_df.loc[gens.index, "carrier"] = "run_of_river"
        for carrier in dispatchable_gens_df.carrier.unique():
            p_nom = dispatchable_gens_df.loc[
                dispatchable_gens_df["carrier"] == carrier, "p_nom"
            ].sum()
            columns_to_aggregate = dispatchable_gens_df[
                dispatchable_gens_df["carrier"] == carrier
            ].index
            dispatchable_gens_df_p[carrier] = (
                etrago_obj.generators_t["p"][columns_to_aggregate].sum(axis="columns")
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

        # Add CHP to conventional generators (only needed in case pf_post_lopf is False,
        # otherwise it is already included above)
        if pf_post_lopf is False:
            chp_df = links_df[
                links_df["carrier"].isin(
                    [
                        "central_gas_CHP",
                        "industrial_gas_CHP",
                        "central_biomass_CHP",
                        "industrial_biomass_CHP",
                    ]
                )
            ]
            if not chp_df.empty:
                # Rename CHP carrier to match with carrier names in eDisGo
                gens_gas_chp = chp_df[
                    chp_df.carrier.isin(["central_gas_CHP", "industrial_gas_CHP"])
                ]
                chp_df.loc[gens_gas_chp.index, "carrier"] = "gas_CHP"
                gens_biomass_chp = chp_df[
                    chp_df.carrier.isin(
                        ["central_biomass_CHP", "industrial_biomass_CHP"]
                    )
                ]
                chp_df.loc[gens_biomass_chp.index, "carrier"] = "biomass_CHP"

                for carrier in chp_df.carrier.unique():
                    p_nom = chp_df.loc[chp_df["carrier"] == carrier, "p_nom"].sum()
                    columns_to_aggregate = chp_df[chp_df["carrier"] == carrier].index
                    dispatchable_gens_df_p[carrier] = abs(
                        etrago_obj.links_t["p1"][columns_to_aggregate].sum(
                            axis="columns"
                        )
                        / p_nom
                    )
                    dispatchable_gens_df_q[carrier] = pd.Series(
                        data=0, index=timeseries_index, dtype=float
                    )

        if (dispatchable_gens_df_p < -1e-3).any().any():
            logger.warning("Dispatchable generator feed-in values smaller -1 kW.")
        results["dispatchable_generators_active_power"] = dispatchable_gens_df_p
        results["dispatchable_generators_reactive_power"] = dispatchable_gens_df_q

    def renewable_generators():

        weather_dep_gens = ["solar", "solar_rooftop", "wind_onshore"]
        renaming_carrier_dict = {
            "solar": ["solar", "solar_rooftop"],
            "wind": ["wind_onshore"],
        }
        weather_dep_gens_df = generators_df[
            generators_df.carrier.isin(weather_dep_gens)
        ]

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
        # potential
        weather_dep_gens_df_pot_p = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=agg_weather_dep_gens_df.carrier.unique(),
        )
        # reactive power
        weather_dep_gens_df_dis_q = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=agg_weather_dep_gens_df.carrier.unique(),
        )
        # curtailment
        weather_dep_gens_df_curt_p = pd.DataFrame(
            0.0,
            index=timeseries_index,
            columns=agg_weather_dep_gens_df.carrier.unique(),
        )

        for index, carrier, p_nom in weather_dep_gens_df[
            ["carrier", "p_nom"]
        ].itertuples():
            # get index in aggregated dataframe to determine total installed capacity
            # of the respective carrier
            agg_idx = agg_weather_dep_gens_df[
                agg_weather_dep_gens_df["carrier"] == carrier
            ].index.values[0]
            p_nom_agg = agg_weather_dep_gens_df.loc[agg_idx, "p_nom"]

            p_series = etrago_obj.generators_t["p"][index]
            p_max_pu_series = etrago_obj.generators_t["p_max_pu"][index]
            p_max_pu_normed_series = p_max_pu_series * p_nom / p_nom_agg

            if pf_post_lopf:
                q_series = etrago_obj.generators_t["q"][index]
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
            else:
                q_normed_series = pd.Series(0.0, index=timeseries_index)

            weather_dep_gens_df_pot_p[carrier] += p_max_pu_normed_series
            weather_dep_gens_df_dis_q[carrier] += q_normed_series
            weather_dep_gens_df_curt_p[carrier] += p_max_pu_series * p_nom - p_series

        if (weather_dep_gens_df_curt_p.min() < -1e-3).any():
            logger.warning("Curtailment values smaller -1 kW.")

        results["renewables_potential"] = weather_dep_gens_df_pot_p
        results["renewables_curtailment"] = weather_dep_gens_df_curt_p
        results["renewables_dispatch_reactive_power"] = weather_dep_gens_df_dis_q
        results["renewables_p_nom"] = agg_weather_dep_gens_df.set_index("carrier").p_nom

    def storages():
        # Filter batteries
        storages_df = etrago_obj.storage_units.loc[
            (etrago_obj.storage_units["carrier"] == "battery")
            & (etrago_obj.storage_units["bus"] == str(bus_id))
        ]
        if not storages_df.empty:
            # p_nom - p_nom_opt can always be used, if extendable is True or False
            storages_df_p_nom = storages_df["p_nom_opt"].sum()
            # Capacity
            storages_df_max_hours = (storages_df["max_hours"]).values[0]
            storages_cap = storages_df_p_nom * storages_df_max_hours
            # p and q
            storages_df_p = etrago_obj.storage_units_t["p"][storages_df.index].sum(
                axis=1
            )
            if pf_post_lopf:
                storages_df_q = etrago_obj.storage_units_t["q"][storages_df.index].sum(
                    axis=1
                )
            else:
                storages_df_q = pd.Series(0.0, index=timeseries_index)
            storages_df_soc = (
                etrago_obj.storage_units_t["state_of_charge"][storages_df.index].sum(
                    axis=1
                )
                / storages_cap
            )

        else:
            storages_df_p_nom = 0
            storages_df_max_hours = 0
            storages_df_p = pd.Series(0.0, index=timeseries_index)
            storages_df_q = pd.Series(0.0, index=timeseries_index)
            storages_df_soc = pd.Series(0.0, index=timeseries_index)
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
            dsm_df_p = etrago_obj.links_t["p0"][dsm_df.index].sum(axis=1)
        else:
            dsm_df_p = pd.Series(0.0, index=timeseries_index)
        results["dsm_active_power"] = dsm_df_p

    def central_heat():

        central_heat_carriers = ["central_heat_pump", "central_resistive_heater"]
        central_heat_df = links_df.loc[
            (links_df["carrier"].isin(central_heat_carriers))
            & (links_df["bus0"] == str(bus_id))
            & (links_df["p_nom"] <= 20)
        ]
        if not central_heat_df.empty:
            # Timeseries
            central_heat_df_p = etrago_obj.links_t["p0"][central_heat_df.index].sum(
                axis=1
            )
            central_heat_df_q = pd.Series(0.0, index=timeseries_index)

            # Nominal power of PtH units
            p_nom = central_heat_df.p_nom.sum()

            # Stores
            central_heat_buses = central_heat_df["bus1"].unique()
            # find all heat stores connected to heat buses
            central_heat_store_links_df = etrago_obj.links.loc[
                etrago_obj.links["bus0"].isin(central_heat_buses)
            ]
            central_heat_store_df = etrago_obj.stores.loc[
                (etrago_obj.stores["carrier"] == "central_heat_store")
                & (
                    etrago_obj.stores["bus"].isin(
                        central_heat_store_links_df.bus1.values
                    )
                )
            ].reset_index(names="store_name")
            central_heat_store_merge_links_df = pd.merge(
                central_heat_store_links_df,
                central_heat_store_df,
                left_on="bus1",
                right_on="bus",
            )
            # capacity
            central_heat_store_capacity = central_heat_store_merge_links_df.set_index(
                "bus0"
            ).e_nom_opt
            # efficiency
            central_heat_store_efficiency = (
                central_heat_store_links_df.efficiency.values[0]
            )
            # SoC
            soc_ts = etrago_obj.stores_t["e"][
                central_heat_store_df.store_name.values
            ].rename(
                columns=central_heat_store_merge_links_df.set_index("store_name").bus0
            )
            soc_ts = soc_ts / central_heat_store_capacity

            # Other feed-in
            dh_feedin_df = pd.DataFrame()
            for heat_bus in central_heat_buses:
                # get feed-in from generators
                heat_gens = etrago_obj.generators[
                    (etrago_obj.generators["bus"] == heat_bus)
                    & (etrago_obj.generators["carrier"] != "load shedding")
                ]
                if not heat_gens.empty:
                    feedin_df_gens = etrago_obj.generators_t["p"][heat_gens.index].sum(
                        axis=1
                    )
                else:
                    feedin_df_gens = pd.Series(0.0, index=timeseries_index)
                # get feed-in from links
                # get all links feeding into heat bus (except heat store)
                heat_links_all = etrago_obj.links[
                    (etrago_obj.links["bus1"] == heat_bus)
                    & (
                        etrago_obj.links["carrier"].isin(
                            [
                                "central_gas_boiler",
                                "central_gas_CHP_heat",
                                "central_heat_pump",
                                "central_resistive_heater",
                            ]
                        )
                    )
                ]
                # filter out PtH units that are already considered in PtH dispatch
                # above
                heat_links = heat_links_all.drop(
                    index=central_heat_df.index, errors="ignore"
                )
                if not heat_links.empty:
                    feedin_df_links = abs(
                        etrago_obj.links_t["p1"][heat_links.index].sum(axis=1)
                    )
                else:
                    feedin_df_links = pd.Series(0.0, index=timeseries_index)
                dh_feedin_df[heat_bus] = feedin_df_gens + feedin_df_links
        else:
            central_heat_df_p = pd.Series(0.0, index=timeseries_index)
            central_heat_df_q = pd.Series(0.0, index=timeseries_index)
            p_nom = 0
            central_heat_store_capacity = pd.Series()
            central_heat_store_efficiency = 0
            soc_ts = pd.DataFrame()
            dh_feedin_df = pd.DataFrame()

        results["heat_pump_central_active_power"] = central_heat_df_p
        results["heat_pump_central_reactive_power"] = central_heat_df_q
        results["heat_pump_central_p_nom"] = p_nom
        results["thermal_storage_central_capacity"] = central_heat_store_capacity
        results["thermal_storage_central_efficiency"] = central_heat_store_efficiency
        results["thermal_storage_central_soc"] = soc_ts
        results["feedin_district_heating"] = dh_feedin_df

    def rural_heat():

        # ToDo (low priority) add resistive heaters (they only exist in eGon100RE)
        rural_heat_carriers = ["rural_heat_pump"]
        rural_heat_df = links_df.loc[
            links_df["carrier"].isin(rural_heat_carriers)
            & (links_df["bus0"] == str(bus_id))
        ]
        if not rural_heat_df.empty:
            # Timeseries
            rural_heat_df_p = etrago_obj.links_t["p0"][rural_heat_df.index].sum(axis=1)
            rural_heat_df_q = pd.Series(0.0, index=timeseries_index)
            # p_nom
            rural_heat_p_nom = rural_heat_df.p_nom.sum()
            # Store
            # capacity
            rural_heat_bus = rural_heat_df["bus1"].values[0]
            rural_heat_store_link_df = etrago_obj.links.loc[
                etrago_obj.links["bus0"] == rural_heat_bus
            ]
            rural_heat_store_df = etrago_obj.stores.loc[
                (etrago_obj.stores["carrier"] == "rural_heat_store")
                & (etrago_obj.stores["bus"] == rural_heat_store_link_df.bus1.values[0])
            ]
            rural_heat_store_capacity = rural_heat_store_df.e_nom_opt.values[0]
            # efficiency
            heat_store_efficiency = rural_heat_store_link_df.efficiency.values[0]
            # SoC
            if rural_heat_store_capacity > 0:
                soc_ts = etrago_obj.stores_t["e"][rural_heat_store_df.index[0]]
                soc_ts = soc_ts / rural_heat_store_capacity
            else:
                soc_ts = pd.Series(0.0, index=timeseries_index)
        else:
            rural_heat_df_p = pd.Series(0.0, index=timeseries_index)
            rural_heat_df_q = pd.Series(0.0, index=timeseries_index)
            rural_heat_p_nom = 0
            rural_heat_store_capacity = 0
            heat_store_efficiency = 0
            soc_ts = pd.Series(0.0, index=timeseries_index)

        results["heat_pump_rural_active_power"] = rural_heat_df_p
        results["heat_pump_rural_reactive_power"] = rural_heat_df_q
        results["heat_pump_rural_p_nom"] = rural_heat_p_nom
        results["thermal_storage_rural_capacity"] = rural_heat_store_capacity
        results["thermal_storage_rural_efficiency"] = heat_store_efficiency
        results["thermal_storage_rural_soc"] = soc_ts

    def bev_charger():
        # BEV charger
        bev_charger_df = links_df.loc[
            (links_df["carrier"] == "BEV_charger") & (links_df["bus0"] == str(bus_id))
        ]
        if not bev_charger_df.empty:
            bev_charger_df_p = etrago_obj.links_t["p0"][bev_charger_df.index].sum(
                axis=1
            )
            bev_charger_df_q = pd.Series(0.0, index=timeseries_index)
        else:
            bev_charger_df_p = pd.Series(0.0, index=timeseries_index)
            bev_charger_df_q = pd.Series(0.0, index=timeseries_index)

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
