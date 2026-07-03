import logging
import subprocess
import sys
import time

from contextlib import contextmanager
from functools import wraps
from pathlib import Path

import saio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def get_engine(config=None):
    """
    Build the database engine from the scenario ``database`` settings.

    Behaviour driven by the ``source`` key of the ``database`` section:

    * ``source`` missing or ``"local"`` — try a local egon-data database via
      SSH tunnel. The config file is taken from ``config_path`` if given,
      otherwise searched at the default location (``EGON_DATA_CONFIG`` env var
      or ``~/.ssh/egon-data.configuration.yaml``). If the config file is not
      found, fall back to the Open Energy Platform (OEP) and log a warning.
    * ``source: "oep"`` — connect to the OEP directly, without a warning.

    A legacy explicit direct-local database (a concrete ``database_name`` plus
    ``host``) is still honoured for backward compatibility.
    """
    db_config = config["database"]
    source = str(db_config.get("source") or "").lower()
    config_path = db_config.get("config_path")

    # Explicit OEP: connect directly, no local attempt and no warning.
    if source == "oep":
        return _oep_engine()

    # Legacy explicit direct local database: a concrete database name plus host
    # is given (e.g. a tunnel ego opened itself via sshtunnel()).
    database_name = db_config.get("database_name")
    placeholders = ("oedb", "<database_name>", "", None)
    if (
        source != "local"
        and database_name not in placeholders
        and db_config.get("host")
    ):
        engine = create_engine(
            f"postgresql+psycopg2://{db_config['user']}:"
            f"{db_config['password']}@{db_config['host']}:"
            f"{int(db_config['port'])}/{database_name}",
            echo=False,
        )
        logger.info(
            f"Local database used: '{database_name}' "
            f"({db_config.get('host')}:{db_config.get('port')})."
        )
        return engine

    # Default (nothing given) or source="local": try the local egon-data
    # database via SSH tunnel, falling back to the OEP (with a warning) when the
    # config file cannot be found.
    from edisgo.io import db as edisgo_db

    if config_path:
        path = Path(config_path).expanduser()
        if not path.is_file():
            return _oep_engine(
                warn_reason=f"egon-data config_path '{config_path}' not found"
            )
    else:
        path = edisgo_db.default_config_path()
        if path is None:
            return _oep_engine(
                warn_reason=(
                    "no egon-data config found (checked EGON_DATA_CONFIG and "
                    f"{edisgo_db.DEFAULT_EGON_DATA_CONFIG})"
                )
            )

    # Reuse eDisGo's proven SSH tunnel + credentials handling so all tools
    # share one configuration.
    engine = edisgo_db.engine(path=path, ssh=True)
    logger.info(
        f"Local database used: '{engine.url.database}' "
        f"(egon-data via SSH tunnel, config {path})."
    )
    return engine


def _oep_engine(warn_reason=None):
    """
    Create an engine for the remote Open Energy Platform (OEP).

    Keeps ego's own OEP URL so :func:`register_tables_in_saio` keeps
    distinguishing the OEP schema from the local egon-data schema correctly.
    A `warn_reason` is logged as a warning when the OEP is used as a fallback.
    """
    if warn_reason:
        logger.warning(f"{warn_reason}; falling back to the OEP.")

    import oedialect  # noqa: F401

    engine = create_engine("postgresql+oedialect://oep.iks.cs.ovgu.de")
    logger.info(f"Created OEP engine: {engine}.")
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
