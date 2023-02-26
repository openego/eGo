# flake8: noqa: E402
import warnings

warnings.filterwarnings("ignore")

import os

import pandas as pd

from edisgo.tools.logger import setup_logger

import ego.mv_clustering.egon_data_io as db_io

from ego.mv_clustering.database import get_engine, register_tables_in_saio, sshtunnel
from ego.tools.utilities import get_scenario_setting

setup_logger(
    loggers=[
        {"name": "root", "file_level": None, "stream_level": "warning"},
        {"name": "ego", "file_level": None, "stream_level": "debug"},
        {"name": "edisgo", "file_level": None, "stream_level": "info"},
    ]
)
base_path = os.path.join(os.path.expanduser("~"), "git-repos", "data", "ego")
config = get_scenario_setting(jsonpath="cluster_setting.json")

with sshtunnel(config=config):
    engine = get_engine(config=config)
    orm = register_tables_in_saio(engine, config=config)

    grid_ids_df = db_io.get_grid_ids(engine=engine, orm=orm)
    solar_capacity_df = db_io.get_solar_capacity(engine=engine, orm=orm)
    wind_capacity_df = db_io.get_wind_capacity(engine=engine, orm=orm)
    emobility_capacity_df = db_io.get_emob_capacity(engine=engine, orm=orm)

    df = pd.concat(
        [grid_ids_df, solar_capacity_df, wind_capacity_df, emobility_capacity_df],
        axis="columns",
    )
    df.fillna(0, inplace=True)

    print("THE END")
