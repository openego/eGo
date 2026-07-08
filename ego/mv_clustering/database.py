import logging
import sys

from contextlib import contextmanager
from functools import wraps

import saio

from edisgo.io.db import engine as edisgo_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def get_engine():
    """
    Return a database engine via eDisGo's source resolution.

    Auto-detects the source: the egon-data database described by the
    configuration file (``~/.ssh/egon-data.configuration.yaml`` or
    ``EGON_DATA_CONFIG``, SSH tunnel included if configured there) if
    such a file exists, otherwise the OEP. Same mechanism as the
    eDisGo runs themselves.
    """
    engine = edisgo_engine()
    logger.info(f"Created engine: {engine}.")
    return engine


@contextmanager
def session_scope(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except:  # noqa: E722
        session.rollback()
        raise
    finally:
        session.close()


def session_decorator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with session_scope(kwargs["engine"]) as session:
            kwargs["session"] = session
            kwargs.pop("engine")
            logger.info(f"Calling {f.__name__}")
            return f(*args, **kwargs)

    return wrapper


def register_tables_in_saio(engine):

    if "oedialect" in str(engine.url):
        db_tables = {
            "egon_mv_grid_district": "edut_00_080",
            "generators_pv_status_quo": "edut_00_156",
            "generators_pv_rooftop": "edut_00_157",
            "generators_wind_status_quo": "edut_00_158",
            "generators": "edut_00_153",
            "etrago_load": "edut_00_067",
            "etrago_load_timeseries": "edut_00_068",
            "heat_pump_capacity_individual": "edut_00_150",
            "pth_capacity_district_heating": "edut_00_065",
        }
        orm = {}

        for name, table_name in db_tables.items():
            saio.register_schema("tables", engine)
            orm[name] = sys.modules["saio.tables"].__getattr__(table_name)
    else:
        db_tables = {
            "egon_mv_grid_district": "grid.egon_mv_grid_district",
            "generators_pv_status_quo": "supply.egon_power_plants_pv",
            "generators_pv_rooftop":
                "supply.egon_power_plants_pv_roof_building",
            "generators_wind_status_quo": "supply.egon_power_plants_wind",
            "generators": "supply.egon_power_plants",
            "etrago_load": "grid.egon_etrago_load",
            "etrago_load_timeseries": "grid.egon_etrago_load_timeseries",
            "heat_pump_capacity_individual": "supply.egon_individual_heating",
            "pth_capacity_district_heating": "grid.egon_etrago_link",
        }
        orm = {}

        for name, table_str in db_tables.items():
            table_list = table_str.split(".")
            table_schema = table_list[0]
            table_name = table_list[1]
            saio.register_schema(table_schema, engine)
            orm[name] = sys.modules[
                f"saio.{table_schema}"].__getattr__(table_name)
    return orm
