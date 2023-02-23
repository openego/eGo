import logging

import pandas as pd

from sqlalchemy import func

from ego.mv_clustering.database import session_decorator

logger = logging.getLogger(__name__)


def func_within(geom_a, geom_b, srid=3035):
    return func.ST_Within(
        func.ST_Transform(
            geom_a,
            srid,
        ),
        func.ST_Transform(
            geom_b,
            srid,
        ),
    )


@session_decorator
def get_grid_ids(orm=None, session=None):
    query = session.query(
        orm["egon_hvmv_substation"].bus_id.label("bus_id"),
        orm["egon_hvmv_substation"].point.label("geom"),
    )
    mv_data = pd.read_sql_query(query.statement, session.bind, index_col="bus_id")
    return mv_data


@session_decorator
def get_solar_capacity(orm=None, session=None):
    # Get PV open space join weather cell id
    query = (
        session.query(
            orm["generators_pv"].bus_id,
            func.sum(orm["generators_pv"].capacity).label("p_openspace"),
        )
        .filter(
            orm["generators_pv"].bus_id > 0,
            orm["generators_pv"].site_type == "Freifläche",
            orm["generators_pv"].status == "InBetrieb",
            orm["generators_pv"].voltage_level.in_([4, 5, 6, 7]),
        )
        .group_by(
            orm["generators_pv"].bus_id,
        )
    )
    generators_pv_open_space_df = pd.read_sql(
        sql=query.statement, con=session.bind, index_col=None
    )

    query = (
        session.query(
            orm["generators_pv_rooftop"].bus_id,
            func.sum(orm["generators_pv_rooftop"].capacity).label("p_rooftop"),
        )
        .filter(
            orm["generators_pv_rooftop"].bus_id > 0,
            orm["generators_pv_rooftop"].scenario == "status_quo",
            orm["generators_pv_rooftop"].voltage_level.in_([4, 5, 6, 7]),
        )
        .group_by(
            orm["generators_pv_rooftop"].bus_id,
        )
    )
    generators_pv_rooftop_df = pd.read_sql(
        sql=query.statement, con=session.bind, index_col=None
    )

    renewable_generators_df = generators_pv_open_space_df.set_index("bus_id").join(
        generators_pv_rooftop_df.set_index("bus_id"), how="outer"
    )
    renewable_generators_df.fillna(value=0, inplace=True)
    renewable_generators_df["solar_cap"] = renewable_generators_df.sum(axis="columns")
    return renewable_generators_df[["solar_cap"]]


@session_decorator
def get_wind_capacity(orm=None, session=None):
    # Get generators wind join weather cells
    query = (
        session.query(
            orm["generators_wind"].bus_id,
            func.sum(orm["generators_wind"].capacity).label("wind_capacity"),
        )
        .filter(
            orm["generators_wind"].bus_id > 0,
            orm["generators_wind"].site_type == "Windkraft an Land",
            orm["generators_wind"].status == "InBetrieb",
            orm["generators_wind"].voltage_level.in_([4, 5, 6, 7]),
        )
        .group_by(
            orm["generators_wind"].bus_id,
        )
    )
    generators_wind_df = pd.read_sql(
        sql=query.statement, con=session.bind, index_col=None
    )

    renewable_generators_df = generators_wind_df.set_index("bus_id")
    renewable_generators_df["wind_cap"] = renewable_generators_df.sum(axis="columns")
    return renewable_generators_df[["wind_cap"]]


@session_decorator
def get_emobility_capacity(orm=None, session=None):
    load_timeseries_nested = (
        session.query(
            orm["etrago_load_timeseries"].scn_name,
            orm["etrago_load_timeseries"].load_id,
            orm["etrago_load_timeseries"].temp_id,
            orm["etrago_load_timeseries"].p_set,
            orm["etrago_load"].bus.label("bus_id"),
        )
        .join(
            orm["etrago_load_timeseries"],
            orm["etrago_load_timeseries"].load_id == orm["etrago_load"].load_id,
        )
        .filter(
            orm["etrago_load"].scn_name == "eGon2035_lowflex",
            orm["etrago_load"].carrier == "land transport EV",
        )
    ).subquery(name="load_timeseries_nested")
    load_timeseries_unnested = (
        session.query(
            load_timeseries_nested.c.bus_id,
            load_timeseries_nested.c.scn_name,
            load_timeseries_nested.c.load_id,
            load_timeseries_nested.c.temp_id,
            func.unnest(load_timeseries_nested.c.p_set).label("p_set"),
        )
    ).subquery(name="load_timeseries_unnested")
    load_timeseries_maximal = (
        session.query(
            load_timeseries_unnested.c.bus_id,
            load_timeseries_unnested.c.scn_name,
            load_timeseries_unnested.c.load_id,
            load_timeseries_unnested.c.temp_id,
            func.max(load_timeseries_unnested.c.p_set).label("p_set_max"),
        ).group_by(
            load_timeseries_unnested.c.bus_id,
            load_timeseries_unnested.c.scn_name,
            load_timeseries_unnested.c.load_id,
            load_timeseries_unnested.c.temp_id,
        )
    ).subquery(name="load_timeseries_maximal")
    load_p_nom = session.query(
        load_timeseries_maximal.c.bus_id,
        func.sum(load_timeseries_maximal.c.p_set_max).label("emob_cap"),
    ).group_by(
        load_timeseries_maximal.c.bus_id,
    )
    emobility_capacity_df = pd.read_sql(
        sql=load_p_nom.statement, con=session.bind, index_col=None
    )
    emobility_capacity_df.set_index("bus_id", inplace=True)
    return emobility_capacity_df


@session_decorator
def get_cummulative_storage_capacity(bus_id_list, orm=None, session=None):
    return
