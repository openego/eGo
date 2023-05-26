import logging
import os
import random

import pandas as pd
import pytest

from pypsa import Network as PyPSANetwork

from ego.tools.interface import ETraGoMinimalData, get_etrago_results_per_bus

logger = logging.getLogger(__name__)

random.seed(42)


class TestSpecs:
    @classmethod
    def setup_class(cls):
        cls.etrago_network = PyPSANetwork(pytest.etrago_test_network_1_path)

    def test_class_etrago_minimal_data(self):
        etrago_network = ETraGoMinimalData(self.etrago_network)
        assert "p_min_pu" not in etrago_network.generators_t

    def test_get_etrago_results_per_bus(self):

        bus_id = 0
        etrago_network = ETraGoMinimalData(self.etrago_network)
        pf_post_lopf = True
        max_cos_phi_renewable = False

        etrago_results_per_bus = get_etrago_results_per_bus(
            bus_id,
            etrago_network,
            pf_post_lopf,
            max_cos_phi_renewable,
        )

        for key, value in etrago_results_per_bus.items():
            logger.info(f"Check Result: {key}")
            if key == "timeindex":
                assert type(value) is pd.DatetimeIndex
                pd.testing.assert_index_equal(
                    value,
                    pd.DatetimeIndex(
                        data=[
                            "2011-01-01 00:00:00",
                            "2011-01-01 12:00:00",
                            "2011-01-02 00:00:00",
                        ],
                        name="snapshot",
                    ),
                )
            elif key == "storage_units_p_nom":
                assert value == 1.0
            elif key == "storage_units_max_hours":
                assert value == 10.0
            elif key == "thermal_storage_central_capacity":
                pd.testing.assert_series_equal(
                    value, pd.Series(index=["4"], data=[1.0]), check_names=False
                )
            elif key == "thermal_storage_rural_capacity":
                assert value == 1.0
            elif key == "heat_pump_rural_p_nom":
                assert value == 1.0
            elif key == "heat_pump_central_p_nom":
                assert value == 2.0
            elif key == "thermal_storage_rural_efficiency":
                assert value == 0.8
            elif key == "thermal_storage_central_efficiency":
                assert value == 0.84
            else:
                path_reference_df = os.path.join(
                    pytest.interface_results_reference_data_path, f"{key}.csv"
                )
                if isinstance(value, pd.DataFrame):
                    reference_df = pd.read_csv(
                        path_reference_df, index_col=0, parse_dates=True
                    )
                    pd.testing.assert_frame_equal(
                        value, reference_df, check_index_type=False, check_names=False
                    )
                else:
                    reference_s = pd.read_csv(
                        path_reference_df, index_col=0, parse_dates=True
                    ).iloc[:, 0]
                    pd.testing.assert_series_equal(
                        value, reference_s, check_index_type=False, check_names=False
                    )

    def test_get_etrago_results_per_bus_empty(self):

        bus_id = 11
        etrago_network = ETraGoMinimalData(self.etrago_network)
        pf_post_lopf = True
        max_cos_phi_renewable = False

        etrago_results_per_bus = get_etrago_results_per_bus(
            bus_id,
            etrago_network,
            pf_post_lopf,
            max_cos_phi_renewable,
        )

        float_results = [
            "storage_units_p_nom",
            "storage_units_max_hours",
            "heat_pump_rural_p_nom",
            "heat_pump_central_p_nom",
            "thermal_storage_rural_capacity",
            "thermal_storage_rural_efficiency",
            "thermal_storage_central_efficiency",
        ]
        series_results = [
            "renewables_p_nom",
            "storage_units_active_power",
            "storage_units_reactive_power",
            "storage_units_soc",
            "dsm_active_power",
            "heat_pump_rural_active_power",
            "heat_pump_rural_reactive_power",
            "thermal_storage_rural_soc",
            "heat_central_active_power",
            "heat_central_reactive_power",
            "thermal_storage_central_capacity",
            "electromobility_active_power",
            "electromobility_reactive_power",
        ]
        dataframes_results = [
            "dispatchable_generators_active_power",
            "dispatchable_generators_reactive_power",
            "renewables_potential",
            "renewables_curtailment",
            "renewables_dispatch_reactive_power",
            "thermal_storage_central_soc",
            "feedin_district_heating",
        ]  #

        for key, value in etrago_results_per_bus.items():
            if key in float_results:
                if value == 0.0:
                    float_results.remove(key)
            elif key in series_results:
                if value.empty:
                    series_results.remove(key)
            elif key in dataframes_results:
                if len(value.columns) == 0:
                    dataframes_results.remove(key)

        assert len(float_results) == 0

    def test_get_etrago_results_per_bus_with_set_max_cosphi(self):

        bus_id = 0
        etrago_network = ETraGoMinimalData(self.etrago_network)
        pf_post_lopf = True
        max_cos_phi_renewable = 0.9

        etrago_results_per_bus = get_etrago_results_per_bus(
            bus_id,
            etrago_network,
            pf_post_lopf,
            max_cos_phi_renewable,
        )
        renewables_dispatch_reactive_power = etrago_results_per_bus[
            "renewables_dispatch_reactive_power"
        ]
        path_reference_df = os.path.join(
            pytest.interface_results_reference_data_path,
            "renewables_dispatch_reactive_power_max_cosphi.csv",
        )
        reference_df = pd.read_csv(path_reference_df, index_col=0, parse_dates=True)
        pd.testing.assert_frame_equal(
            renewables_dispatch_reactive_power,
            reference_df,
            check_index_type=False,
            check_names=False,
            atol=1e-4,
        )
