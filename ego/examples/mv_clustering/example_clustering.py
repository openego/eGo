# flake8: noqa: E402
import warnings

warnings.filterwarnings("ignore")

import os

from edisgo.tools.logger import setup_logger

from ego.mv_clustering import cluster_workflow
from ego.tools.utilities import get_scenario_setting

setup_logger(
    loggers=[
        {"name": "root", "file_level": None, "stream_level": "warning"},
        {"name": "ego", "file_level": None, "stream_level": "debug"},
        {"name": "edisgo", "file_level": None, "stream_level": "info"},
    ]
)

base_path = os.path.join(os.path.expanduser("~"), "git-repos", "data", "ego")

os.remove(os.path.join(base_path, "ding0_path", "attributes.csv"))

config = get_scenario_setting(jsonpath="cluster_setting.json")

cluster_workflow(config=config)

print("THE END")
