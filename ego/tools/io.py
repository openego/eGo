"""
Input &  output functions of eGo

"""
__copyright__ = "ZNES"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__url__ = "https://github.com/openego/data_processing/blob/master/LICENSE"
__author__ = "wolfbunke"

#from etrago.tools.io import
#from egoio.db_tables.model_draft import NetworkScenario, results_to_oedb
import os
if not 'READTHEDOCS' in os.environ:
    import pyproj as proj
    from shapely.geometry import Polygon, Point, MultiPolygon
    from sqlalchemy import MetaData, create_engine, func
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.automap import automap_base
    from geoalchemy2 import Geometry, shape # Geometry type used by SQLA
    from geoalchemy2 import *
    import geopandas as gpd
    from egoio.db_tables.model_draft import RenpassGisParameterRegion
    import pandas as pd
    from egoio.tools import db


def geolocation_buses(network, session):
    """
    Use Geometries of buses x/y (lon/lat) and Polygons
    of Countries from RenpassGisParameterRegion
    in order to locate the buses

    ToDo:
    1) check eTrago stack generation plots and
       other in order of adaptation


    """
    # Start db connetion
    # get renpassG!S scenario data


    meta = MetaData()
    meta.bind = session.bind
    conn = meta.bind
    # get db table
    meta.reflect(bind=conn, schema='model_draft',
                 only=['renpass_gis_parameter_region'])

    # map to classes
    Base = automap_base(metadata=meta)
    Base.prepare()
    RenpassGISRegion = \
        Base.classes.renpass_gis_parameter_region

    # Define regions
    region_id = ['DE','DK', 'FR', 'BE', 'LU', \
                 'NO', 'PL', 'CH', 'CZ', 'SE', 'NL']

    query = session.query(RenpassGISRegion.gid, RenpassGISRegion.u_region_id,
                       RenpassGISRegion.stat_level, RenpassGISRegion.geom,
                       RenpassGISRegion.geom_point)

    # get regions by query and filter
    Regions =  [(gid, u_region_id, stat_level, shape.to_shape(geom),\
                shape.to_shape(geom_point)) for gid, u_region_id, stat_level,\
                 geom, geom_point in query.filter(RenpassGISRegion.u_region_id.\
                 in_(region_id)).all()]

    crs = {'init': 'epsg:4326'}
    # transform lon lat to shapely Points and create GeoDataFrame
    points = [Point(xy) for xy in zip( network.buses.x,  network.buses.y)]
    bus = gpd.GeoDataFrame(network.buses, crs=crs, geometry=points)
    # Transform Countries Polygons as Regions
    region = pd.DataFrame(Regions, columns=['id','country','stat_level','Polygon','Point'])
    re = gpd.GeoDataFrame(region, crs=crs, geometry=region['Polygon'])
    # join regions and buses by geometry which intersects
    busC = gpd.sjoin(bus, re, how='inner', op='intersects')
    #busC
    # Drop non used columns
    busC = busC.drop(['index_right', 'Point', 'id', 'Polygon', 'stat_level','geometry'], axis=1)
    # add busC to eTraGo.buses
    network.buses['country_code'] = busC['country']

    # close session
    session.close()

    return network



def results_to_excel(results):
    """

    """


    # Write the results as xlsx file
    # ToDo add time of calculation to file name
    # add xlsxwriter to setup
    writer = pd.ExcelWriter('open_ego_results.xlsx', engine='xlsxwriter')

    # write results of installed Capacity by fuels
    results.total.to_excel(writer, index=False, sheet_name='Total Calculation')

    # write orgininal data in second sheet
    results.to_excel(writer, index=True, sheet_name='Results by carriers')
    #add plots

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    # buses
