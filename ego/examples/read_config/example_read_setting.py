# flake8: noqa: E402
import warnings

warnings.filterwarnings("ignore")

from edisgo.tools.logger import setup_logger

from ego.tools.utilities import get_scenario_setting

setup_logger(
    loggers=[
        {"name": "root", "file_level": None, "stream_level": "warning"},
        {"name": "ego", "file_level": None, "stream_level": "debug"},
        {"name": "edisgo", "file_level": None, "stream_level": "info"},
    ]
)

config = get_scenario_setting(jsonpath="external_config_setting.json")

config = get_scenario_setting(jsonpath="no_external_config_setting.json")

print("THE END")
