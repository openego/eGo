import logging

import pytest

from edisgo.run.config import load_config
from edisgo.run.validator import validate

from ego.tools.edisgo_integration import EDisGoNetworks

logger = logging.getLogger(__name__)


def _make_networks(edisgo_args):
    """
    Build an EDisGoNetworks instance without running __init__ (which would
    immediately kick off a full eDisGo pool run) - only the attributes
    _build_run_edisgo_config actually reads are set.
    """
    networks = EDisGoNetworks.__new__(EDisGoNetworks)
    networks._json_file = {"eDisGo": edisgo_args}
    networks._scn_name = "eGon2035"
    networks._grid_path = "/some/grid/path"
    networks._results = "/some/results/path"
    networks._preset = edisgo_args.get("preset")
    return networks


class TestBuildRunEdisgoConfig:
    def test_no_spatial_reduction_block_when_absent(self):
        networks = _make_networks({"preset": "overlying_grid_opf_spatial"})
        cfg = networks._build_run_edisgo_config(32377)
        assert "spatial_reduction" not in cfg

    def test_default_spatial_reduction_applied_to_every_grid(self):
        default = {"enabled": True, "mode": "kmeansdijkstra", "reduction_factor": 0.3}
        networks = _make_networks(
            {"preset": "overlying_grid_opf_spatial", "spatial_reduction": default}
        )
        assert networks._build_run_edisgo_config(32377)["spatial_reduction"] == default
        assert networks._build_run_edisgo_config(32355)["spatial_reduction"] == default

    def test_per_grid_override_is_merged_into_default(self):
        default = {"enabled": True, "mode": "kmeansdijkstra", "reduction_factor": 0.3}
        networks = _make_networks(
            {
                "preset": "overlying_grid_opf_spatial",
                "spatial_reduction": default,
                "spatial_reduction_per_grid": {"32355": {"enabled": False}},
            }
        )
        # listed grid gets the default with the overridden key
        assert networks._build_run_edisgo_config(32355)["spatial_reduction"] == {
            **default,
            "enabled": False,
        }
        # unlisted grid still gets the default
        assert networks._build_run_edisgo_config(32377)["spatial_reduction"] == default

    def test_non_mapping_rejected(self):
        # false would otherwise turn into an empty block that keeps the
        # preset's enabled reduction
        networks = _make_networks(
            {"preset": "overlying_grid_opf_spatial", "spatial_reduction": False}
        )
        with pytest.raises(ValueError, match="must be a mapping or null"):
            networks._build_run_edisgo_config(32377)

    def test_old_timeseries_selection_key_rejected(self):
        networks = _make_networks(
            {"preset": "overlying_grid_opf_spatial", "timeseries_selection": {}}
        )
        with pytest.raises(ValueError, match="renamed to 'timestep_selection'"):
            networks._build_run_edisgo_config(32377)

    def test_omitted_entirely_if_neither_default_nor_override_set(self):
        networks = _make_networks(
            {
                "preset": "overlying_grid_opf_spatial",
                "spatial_reduction_per_grid": {"32355": {"enabled": False}},
            }
        )
        # 32355 has an explicit override -> present
        assert "spatial_reduction" in networks._build_run_edisgo_config(32355)
        # 32377 has neither a default nor an override -> key omitted, letting
        # the eDisGo preset's own default apply
        assert "spatial_reduction" not in networks._build_run_edisgo_config(32377)


CRITICAL = {
    "task": "select_critical_timesteps",
    "select_critical_timesteps": {"method": "power_flow"},
}


class TestTimestepSelection:
    def test_default_applied_to_every_grid(self):
        networks = _make_networks(
            {
                "preset": "overlying_grid_opf_spatial",
                "timestep_selection": CRITICAL,
            }
        )
        for grid in (32377, 32355):
            cfg = networks._build_run_edisgo_config(grid)
            assert cfg["timestep_selection"] == CRITICAL

    def test_per_grid_override_is_merged_into_default(self):
        networks = _make_networks(
            {
                "preset": "overlying_grid_opf_spatial",
                "timestep_selection": CRITICAL,
                "timestep_selection_per_grid": {
                    "32355": {"select_critical_timesteps": {"percentage": 0.5}}
                },
            }
        )
        cfg = networks._build_run_edisgo_config(32355)
        assert cfg["timestep_selection"] == {
            "task": "select_critical_timesteps",
            "select_critical_timesteps": {"method": "power_flow", "percentage": 0.5},
        }
        cfg = networks._build_run_edisgo_config(32377)
        assert cfg["timestep_selection"] == CRITICAL

    def test_ego_settings_override_preset(self):
        # spatial_reduction_opf runs set_timeindex by default
        networks = _make_networks(
            {"preset": "spatial_reduction_opf", "timestep_selection": CRITICAL}
        )
        cfg = load_config(networks._build_run_edisgo_config(32377))
        validate(cfg)
        assert cfg["timestep_selection"]["task"] == "select_critical_timesteps"
        assert cfg["timestep_selection"]["select_critical_timesteps"] == {
            "method": "power_flow"
        }


class TestDatabase:
    def test_no_database_block_when_absent(self):
        networks = _make_networks({"preset": "overlying_grid_opf_spatial"})
        assert "database" not in networks._build_run_edisgo_config(32377)

    def test_source_string_overrides_preset(self):
        # spatial_reduction_opf uses the egon-data database by default
        networks = _make_networks(
            {"preset": "spatial_reduction_opf", "database": "oep"}
        )
        cfg = load_config(networks._build_run_edisgo_config(32377))
        assert cfg["database"]["source"] == "oep"


def test_grid_configs_share_no_objects():
    """Changing one grid's config must not change another grid's config or
    the scenario settings."""
    networks = _make_networks(
        {"preset": "overlying_grid_opf_spatial", "timestep_selection": CRITICAL}
    )
    first = networks._build_run_edisgo_config(32377)
    first["timestep_selection"]["select_critical_timesteps"]["method"] = "x"
    second = networks._build_run_edisgo_config(32355)
    assert second["timestep_selection"] == CRITICAL
    assert CRITICAL["select_critical_timesteps"]["method"] == "power_flow"
