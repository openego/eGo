import logging
import subprocess
import sys
import time

from contextlib import contextmanager
from functools import wraps

import saio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def get_engine(config=None):
    config = config["database"]

    if config["database_name"] == "oedb":
        import oedialect
        engine = create_engine("postgresql+oedialect://oep.iks.cs.ovgu.de")
    else:
        engine = create_engine(
            f"postgresql+psycopg2://{config['user']}:"
            f"{config['password']}@{config['host']}:"
            f"{int(config['port'])}/{config['database_name']}",
            echo=False,
        )
    logger.info(f"Created engine: {engine}.")
    return engine


@contextmanager
def sshtunnel(config=None):
    ssh_config = config["ssh"]
    if ssh_config["enabled"]:
        try:
            logger.info("Open ssh tunnel.")
            proc = subprocess.Popen(
                [
                    "ssh",
                    "-N",
                    "-L",
                    f"{ssh_config['local_port']}"
                    f":{ssh_config['local_address']}"
                    f":{ssh_config['port']}",
                    f"{ssh_config['user']}@{ssh_config['ip']}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(2)
            yield proc
        finally:
            logger.info("Close ssh tunnel.")
            proc.kill()
            outs, errs = proc.communicate()
            logger.info(
                f"SSH process output STDOUT:{outs.decode('utf-8')}, "
                f"STDERR:{errs.decode('utf-8')}"
            )
    else:
        try:
            logger.info("Don't use an ssh tunnel.")
            yield None
        finally:
            logger.info("Close contextmanager.")


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

    if "oep.iks.cs.ovgu.de" in str(engine.url):
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
