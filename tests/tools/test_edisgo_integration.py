import logging

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
        networks = _make_networks({"preset": "uc5_select_timesteps"})
        cfg = networks._build_run_edisgo_config(32377)
        assert "spatial_reduction" not in cfg

    def test_default_spatial_reduction_applied_to_every_grid(self):
        default = {"enabled": True, "mode": "kmeansdijkstra", "reduction_factor": 0.3}
        networks = _make_networks(
            {"preset": "uc6_spatial_reduction", "spatial_reduction": default}
        )
        assert networks._build_run_edisgo_config(32377)["spatial_reduction"] == default
        assert networks._build_run_edisgo_config(32355)["spatial_reduction"] == default

    def test_per_grid_override_wins_for_listed_grid(self):
        default = {"enabled": True, "mode": "kmeansdijkstra", "reduction_factor": 0.3}
        override = {"enabled": False}
        networks = _make_networks(
            {
                "preset": "uc6_spatial_reduction",
                "spatial_reduction": default,
                "spatial_reduction_per_grid": {"32355": override},
            }
        )
        # listed grid gets the override, whole-block replacement (not merged)
        assert networks._build_run_edisgo_config(32355)["spatial_reduction"] == override
        # unlisted grid still gets the default
        assert networks._build_run_edisgo_config(32377)["spatial_reduction"] == default

    def test_omitted_entirely_if_neither_default_nor_override_set(self):
        networks = _make_networks(
            {
                "preset": "uc6_spatial_reduction",
                "spatial_reduction_per_grid": {"32355": {"enabled": False}},
            }
        )
        # 32355 has an explicit override -> present
        assert "spatial_reduction" in networks._build_run_edisgo_config(32355)
        # 32377 has neither a default nor an override -> key omitted, letting
        # the eDisGo preset's own default apply
        assert "spatial_reduction" not in networks._build_run_edisgo_config(32377)
