import logging

import pandas as pd

from sqlalchemy import func

from ego.mv_clustering.database import session_decorator

logger = logging.getLogger(__name__)


def func_within(geom_a, geom_b, srid=3035):
    """
    Checks if geometry a is completely within geometry b.

    Parameters
    ----------
    geom_a : Geometry
        Geometry within `geom_b`.
    geom_b : Geometry
        Geometry containing `geom_a`.
    srid : int
        SRID geometries are transformed to in order to use the same SRID for both
        geometries.

    """
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
    """
    Gets all MV grid IDs and the area of each grid in m^2.

    Parameters
    -----------
    orm : dict
        Dictionary with tables to retrieve data from.

    Returns
    -------
    pandas.DataFrame
        Dataframe with grid ID in index and corresponding area in m^2 in column
        "area_m2".

    """
    query = session.query(
        orm["egon_mv_grid_district"].bus_id,
        orm["egon_mv_grid_district"].area.label("area_m2"),
    )
    return pd.read_sql_query(query.statement, session.bind, index_col="bus_id")


@session_decorator
def get_solar_capacity(scenario, grid_ids, orm=None, session=None):
    """
    Gets PV capacity (rooftop and ground mounted) in MW per grid in specified scenario.

    Parameters
    -----------
    scenario : str
        Scenario to obtain data for. Possible options are "status_quo", "eGon2035",
        and "eGon100RE".
    grid_ids : list(int)
        List of grid IDs to obtain data for.
    orm : dict
        Dictionary with tables to retrieve data from.

    Returns
    -------
    pandas.DataFrame
        DataFrame with grid ID in index and corresponding PV capacity in MW in column
        "pv_capacity_mw".

    """
    # get PV ground mounted capacity per grid
    if scenario == "status_quo":
        query = (
            session.query(
                orm["generators_pv_status_quo"].bus_id,
                func.sum(orm["generators_pv_status_quo"].capacity).label("p_openspace"),
            )
            .filter(
                orm["generators_pv_status_quo"].bus_id.in_(grid_ids),
                orm["generators_pv_status_quo"].site_type == "Freifläche",
                orm["generators_pv_status_quo"].status == "InBetrieb",
                orm["generators_pv_status_quo"].capacity <= 20,
                orm["generators_pv_status_quo"].voltage_level.in_([4, 5, 6, 7]),
            )
            .group_by(
                orm["generators_pv_status_quo"].bus_id,
            )
        )
        cap_open_space_df = pd.read_sql(
            sql=query.statement, con=session.bind, index_col="bus_id"
        )
    else:
        query = (
            session.query(
                orm["generators"].bus_id,
                func.sum(orm["generators"].el_capacity).label("p_openspace"),
            )
            .filter(
                orm["generators"].scenario == scenario,
                orm["generators"].bus_id.in_(grid_ids),
                orm["generators"].voltage_level >= 4,
                orm["generators"].el_capacity <= 20,
                orm["generators"].carrier == "solar",
            )
            .group_by(
                orm["generators"].bus_id,
            )
        )
        cap_open_space_df = pd.read_sql(
            sql=query.statement, con=session.bind, index_col="bus_id"
        )
    # get PV rooftop capacity per grid
    query = (
        session.query(
            orm["generators_pv_rooftop"].bus_id,
            func.sum(orm["generators_pv_rooftop"].capacity).label("p_rooftop"),
        )
        .filter(
            orm["generators_pv_rooftop"].bus_id.in_(grid_ids),
            orm["generators_pv_rooftop"].scenario == scenario,
            orm["generators_pv_rooftop"].capacity <= 20,
            orm["generators_pv_rooftop"].voltage_level.in_([4, 5, 6, 7]),
        )
        .group_by(
            orm["generators_pv_rooftop"].bus_id,
        )
    )
    cap_rooftop_df = pd.read_sql(
        sql=query.statement, con=session.bind, index_col="bus_id"
    )

    return (
        cap_open_space_df.join(cap_rooftop_df, how="outer")
        .fillna(value=0)
        .sum(axis="columns")
        .to_frame("pv_capacity_mw")
    )


@session_decorator
def get_wind_capacity(scenario, grid_ids, orm=None, session=None):
    """
    Gets wind onshore capacity in MW per grid in specified scenario.

    Parameters
    -----------
    scenario : str
        Scenario to obtain data for. Possible options are "status_quo", "eGon2035",
        and "eGon100RE".
    grid_ids : list(int)
        List of grid IDs to obtain data for.
    orm : dict
        Dictionary with tables to retrieve data from.

    Returns
    -------
    pandas.DataFrame
        DataFrame with grid ID in index and corresponding Wind capacity in MW in
        column "wind_capacity_mw".

    """
    if scenario == "status_quo":
        query = (
            session.query(
                orm["generators_wind_status_quo"].bus_id,
                func.sum(orm["generators_wind_status_quo"].capacity).label(
                    "wind_capacity_mw"
                ),
            )
            .filter(
                orm["generators_wind_status_quo"].bus_id.in_(grid_ids),
                orm["generators_wind_status_quo"].site_type == "Windkraft an Land",
                orm["generators_wind_status_quo"].status == "InBetrieb",
                orm["generators_wind_status_quo"].capacity <= 20,
                orm["generators_wind_status_quo"].voltage_level.in_([4, 5, 6, 7]),
            )
            .group_by(
                orm["generators_wind_status_quo"].bus_id,
            )
        )
        cap_wind_df = pd.read_sql(
            sql=query.statement, con=session.bind, index_col="bus_id"
        )
    else:
        query = (
            session.query(
                orm["generators"].bus_id,
                func.sum(orm["generators"].el_capacity).label("wind_capacity_mw"),
            )
            .filter(
                orm["generators"].scenario == scenario,
                orm["generators"].bus_id.in_(grid_ids),
                orm["generators"].voltage_level >= 4,
                orm["generators"].el_capacity <= 20,
                orm["generators"].carrier == "wind_onshore",
            )
            .group_by(
                orm["generators"].bus_id,
            )
        )
        cap_wind_df = pd.read_sql(
            sql=query.statement, con=session.bind, index_col="bus_id"
        )
    return cap_wind_df


@session_decorator
def get_electromobility_maximum_load(scenario, grid_ids, orm=None, session=None):
    """
    Parameters
    -----------
    scenario : str
        Scenario to obtain data for. Possible options are "status_quo", "eGon2035",
        and "eGon100RE".
    grid_ids : list(int)
        List of grid IDs to obtain data for.
    orm : dict
        Dictionary with tables to retrieve data from.

    Returns
    -------
    pandas.DataFrame
        DataFrame with grid ID in index and corresponding maximum electromobility load
        in MW in column "electromobility_max_load_mw".

    """
    if scenario == "status_quo":
        return pd.DataFrame(columns=["electromobility_max_load_mw"])
    else:
        load_timeseries_nested = (
            session.query(
                orm["etrago_load"].bus.label("bus_id"),
                orm["etrago_load_timeseries"].p_set,
            )
            .join(
                orm["etrago_load_timeseries"],
                orm["etrago_load_timeseries"].load_id == orm["etrago_load"].load_id,
            )
            .filter(
                orm["etrago_load"].scn_name == f"{scenario}_lowflex",
                orm["etrago_load"].carrier == "land_transport_EV",
                orm["etrago_load"].bus.in_(grid_ids),
            )
        ).subquery(name="load_timeseries_nested")
        load_timeseries_unnested = (
            session.query(
                load_timeseries_nested.c.bus_id,
                func.unnest(load_timeseries_nested.c.p_set).label("p_set"),
            )
        ).subquery(name="load_timeseries_unnested")
        load_timeseries_maximal = (
            session.query(
                load_timeseries_unnested.c.bus_id,
                func.max(load_timeseries_unnested.c.p_set).label("p_set_max"),
            ).group_by(
                load_timeseries_unnested.c.bus_id,
            )
        ).subquery(name="load_timeseries_maximal")
        load_p_nom = session.query(
            load_timeseries_maximal.c.bus_id,
            load_timeseries_maximal.c.p_set_max.label("electromobility_max_load_mw"),
        )
        return pd.read_sql(
            sql=load_p_nom.statement, con=session.bind, index_col="bus_id"
        )


@session_decorator
def get_pth_capacity(scenario, grid_ids, orm=None, session=None):
    """
    Gets PtH capacity (individual heating and district heating) in MW per grid
    in specified scenario.

    Parameters
    -----------
    scenario : str
        Scenario to obtain data for. Possible options are "status_quo", "eGon2035",
        and "eGon100RE".
    grid_ids : list(int)
        List of grid IDs to obtain data for.
    orm : dict
        Dictionary with tables to retrieve data from.

    Returns
    -------
    pandas.DataFrame
        DataFrame with grid ID in index and corresponding PtH capacity in MW in
        column "pth_capacity_mw".

    """
    if scenario == "status_quo":
        return pd.DataFrame(columns=["pth_capacity_mw"])
    else:
        # get individual heat pump capacity
        query = (
            session.query(
                orm["heat_pump_capacity_individual"].mv_grid_id.label("bus_id"),
                func.sum(orm["heat_pump_capacity_individual"].capacity).label(
                    "cap_individual"
                ),
            )
            .filter(
                orm["heat_pump_capacity_individual"].mv_grid_id.in_(grid_ids),
                orm["heat_pump_capacity_individual"].carrier == "heat_pump",
                orm["heat_pump_capacity_individual"].scenario == scenario,
                orm["heat_pump_capacity_individual"].capacity <= 17.5,
            )
            .group_by(
                orm["heat_pump_capacity_individual"].mv_grid_id,
            )
        )
        cap_individual_df = pd.read_sql(
            sql=query.statement, con=session.bind, index_col="bus_id"
        )
        # get central heat pump and resistive heater capacity
        query = (
            session.query(
                orm["pth_capacity_district_heating"].bus0,
                func.sum(orm["pth_capacity_district_heating"].p_nom).label("p_set"),
            )
            .filter(
                orm["pth_capacity_district_heating"].bus0.in_(grid_ids),
                orm["pth_capacity_district_heating"].scn_name == scenario,
                orm["pth_capacity_district_heating"].carrier.in_(
                    ["central_heat_pump", "central_resistive_heater"]
                ),
                orm["pth_capacity_district_heating"].p_nom <= 17.5,
            )
            .group_by(
                orm["pth_capacity_district_heating"].bus0,
            )
        )
        cap_dh_df = pd.read_sql(sql=query.statement, con=session.bind, index_col="bus0")
    return (
        cap_individual_df.join(cap_dh_df, how="outer")
        .fillna(value=0)
        .sum(axis="columns")
        .to_frame("pth_capacity_mw")
    )
