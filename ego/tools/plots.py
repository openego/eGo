# -*- coding: utf-8 -*-
# Copyright 2016-2018 Europa-Universität Flensburg,
# Flensburg University of Applied Sciences,
# Centre for Sustainable Energy Systems
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# File description
"""Module which collects useful functions for plotting eTraGo, eDisGo and
eGo results.
"""

import numpy as np
import pandas as pd
import os
geopandas = True

if not 'READTHEDOCS' in os.environ:
    from etrago.tools.plot import (plot_line_loading, plot_stacked_gen,
                                   add_coordinates, curtailment, gen_dist,
                                   storage_distribution,
                                   plot_voltage, plot_residual_load)
    from ego.tools.economics import etrago_convert_overnight_cost
    import pyproj as proj
    from math import sqrt, log10
    from shapely.geometry import Polygon, Point, MultiPolygon
    from geoalchemy2 import *
    try:
        import geopandas as gpd
        import folium
        from folium import plugins
        import branca.colormap as cm
    except:
        geopandas = False
    import oedialect
    import webbrowser
    from egoio.db_tables.model_draft import (
        EgoGridMvGriddistrict, RenpassGisParameterRegion)
    from egoio.db_tables.grid import EgoDpMvGriddistrict
    import matplotlib.pyplot as plt
    import matplotlib as mpl

import logging
logger = logging.getLogger('ego')

__copyright__ = "Flensburg University of Applied Sciences, Europa-Universität"\
    "Flensburg, Centre for Sustainable Energy Systems"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolfbunke"


# plot colore of Carriers
def carriers_colore():
    """ Return matplotlib colore set per carrier (technologies of
    generators) of eTraGo.

    Returns
    -------
    colors :  :obj:`dict`
        List of carriers and matplotlib colores
    """

    colors = {'biomass': 'green',
              'coal': 'k',
              'gas': 'orange',
              'eeg_gas': 'olive',
              'geothermal': 'purple',
              'lignite': 'brown',
              'oil': 'darkgrey',
              'other_non_renewable': 'pink',
              'reservoir': 'navy',
              'run_of_river': 'aqua',
              'pumped_storage': 'steelblue',
              'solar': 'yellow',
              'uranium': 'lime',
              'waste': 'sienna',
              'wind': 'skyblue',
              'slack': 'pink',
              'load shedding': 'red',
              'nan': 'm',
              'imports': 'salmon',
              '': 'm'}

    return colors


def ego_colore():
    """ Get the four eGo colores

    Returns
    -------
    colors :  :obj:`dict`
        List of eGo matplotlib colores
    """
    colors = {'egoblue1': '#1F567D',
              'egoblue2': '#84A2B8',
              'egoblue3': '#A3B9C9',
              'egoblue4': '#C7D5DE'
              }

    return colors


def plot_storage_expansion(ego, filename=None, dpi=300,
                           column='overnight_costs',
                           scaling=1):
    """ Plot line expantion

    Parameters
    ----------
    ego : :class:`ego.tools.io.eGo`
        eGo ``eGo`` inclueds on eTraGo and eDisGo
    filename: list
        Filename and/or path of location to store graphic
    dpi: int
        dpi value of graphic
    column: str
        column name of eTraGo's line costs. Default: ``overnight_costs`` in EURO.
        Also available ``s_nom_expansion`` in MVA or
        annualized ``investment_costs`` in EURO
    scaling: numeric
        Factor to scale storage size of bus_sizes

    Returns
    -------
    plot :obj:`matplotlib.pyplot.show`
            https://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.show
    """

    network = ego.etrago.network
    json_file = ego.json_file

    # get storage values
    if 'storages' in ego.json_file['eTraGo']['extendable']:
        storage_inv = network.storage_units[network.storage_units.
                                            capital_cost > 0.]
        storage_inv['investment_costs'] = (storage_inv.capital_cost *
                                           storage_inv.p_nom_opt)
        storage_inv['overnight_costs'] = etrago_convert_overnight_cost(
            storage_inv['investment_costs'], json_file)

    msd_max = storage_inv[column].max()
    msd_median = storage_inv[column].median()
    msd_min = storage_inv[column].min()

    if (msd_max - msd_min) > 1.e+5:

        if msd_max != 0:
            LabelVal = int(log10(msd_max))
        else:
            LabelVal = 0
        if LabelVal < 0:
            LabelUnit = '€'
            msd_max, msd_median, msd_min = msd_max * \
                1000, msd_median * 1000, msd_min * 1000
            storage_inv[column] = storage_inv[column] * 1000
        elif LabelVal < 3:
            LabelUnit = 'k €'
        else:
            LabelUnit = 'M €'
            msd_max, msd_median, msd_min = msd_max / \
                1000, msd_median / 1000, msd_min / 1000
            storage_inv[column] = storage_inv[column] / 1000
    else:
        LabelUnit = '€'

    # start plotting
    figsize = 6, 6
    fig, ax = plt.subplots(1, 1, figsize=(figsize))

    bus_sizes = storage_inv[column] * scaling

    if column == 'investment_costs':
        title = 'Annualized Storage costs per timestep'
        ltitel = 'Storage costs'
    if column == 'overnight_costs':
        title = 'Total Expansion Costs Overnight'
        ltitel = 'Storage costs'
    if column == 'p_nom_opt':
        title = 'Storage Expansion in MVA'
        ltitel = 'Storage size'
        LabelUnit = 'kW'
    if column not in ['investment_costs', 'overnight_costs', 'p_nom_opt']:
        title = 'unknown'
        ltitel = 'unknown'
        LabelUnit = 'unknown'

    if sum(storage_inv[column]) == 0:
        sc = network.plot(bus_sizes=0,
                          ax=ax,
                          title="No storage expantion")
    else:
        sc = network.plot(
            bus_sizes=bus_sizes,
            bus_colors='g',
            # bus_cmap=
            # line_colors='gray',
            title=title,
            line_widths=0.3
        )

    ax.set_alpha(0.4)

    # add legend
    for area in [msd_max, msd_median, msd_min]:
        plt.scatter([], [], c='white', s=area * scaling,
                    label='= ' + str(round(area, 0)) + LabelUnit + ' ')

    plt.legend(scatterpoints=1,
               labelspacing=1,
               title=ltitel,
               loc='upper left',
               shadow=True,
               fontsize='x-large')

    ax.autoscale(tight=True)

    if filename is None:
        plt.show()
    else:
        fig = ax.get_figure()
        fig.set_size_inches(10, 8, forward=True)
        fig.savefig(filename,  dpi=dpi)
        plt.close()


def plot_line_expansion(ego, filename=None, dpi=300, column='overnight_costs'):
    """ Plot line expantion

    Parameters
    ----------
    ego : :class:`ego.tools.io.eGo`
        eGo  ``eGo`` inclueds on eTraGo and eDisGo
    filename: list
        Filename and or path of location to store graphic
    dpi: int
        dpi value of graphic
    column: str
        column name of eTraGo's line costs. Default: ``overnight_costs`` in EURO.
        Also available ``s_nom_expansion`` in MVA or
        annualized ``investment_costs`` in EURO

    Returns
    -------
    plot :obj:`matplotlib.pyplot.show`
            https://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.show
    """

    network = ego.etrago.network
    json_file = ego.json_file

    # get values
    if 'network' in ego.json_file['eTraGo']['extendable']:
        network.lines['s_nom_expansion'] = network.lines.s_nom_opt.subtract(
            network.lines.s_nom, axis='index')
        network.lines['investment_costs'] = network.lines.s_nom_expansion.\
            multiply(network.lines.capital_cost, axis='index')
        network.lines['overnight_costs'] = etrago_convert_overnight_cost(
            network.lines['investment_costs'], json_file)

    else:
        network.lines['s_nom_expansion'] = None
        network.lines['investment_costs'] = None
        network.lines['overnight_costs'] = None

    # start plotting
    figsize = 10, 8
    fig, ax = plt.subplots(1, 1, figsize=(figsize))

    cmap = plt.cm.jet

    if column == 's_nom_expansion':
        line_value = network.lines[column]
        title = "Line expansion in MVA"
    if column == 'overnight_costs':
        line_value = network.lines[column]
        title = "Total Expansion Costs in € per line"
    if column == 'investment_costs':
        line_value = network.lines[column]
        title = "Annualized Expansion Costs in € per line and time step"

    line_widths = (line_value/line_value.max())

    lc = network.plot(ax=ax, line_colors=line_value,
                      line_cmap=cmap,
                      title=title,
                      line_widths=line_widths)

    boundaries = [min(line_value),
                  max(line_value)]

    v = np.linspace(boundaries[0], boundaries[1], 101)

    # colorbar
    cb = plt.colorbar(lc[1], boundaries=v,
                      ticks=v[0:101:10],
                      ax=ax)
    cb.set_clim(vmin=boundaries[0], vmax=boundaries[1])

    if column == 's_nom_expansion':
        cb.set_label('Expansion in MVA per line')
    if column == 'overnight_costs':
        cb.set_label('Total Expansion Costs in € per line')
    if column == 'investment_costs':
        cb.set_label('Annualized Expansion Costs in € per line')

    ax.autoscale(tight=True)

    if filename is None:
        plt.show()
    else:
        fig = ax.get_figure()
        fig.set_size_inches(10, 8, forward=True)
        fig.savefig(filename,  dpi=dpi)
        plt.close()


def plot_grid_storage_investment(costs_df, filename, display, var=None):
    """
    """
    colors = ego_colore()
    bar_width = 0.35
    opacity = 0.4

    if var == 'overnight_cost':
        tic = costs_df[['component',
                        'overnight_costs',
                        'voltage_level']]
        tic.set_index(['voltage_level', 'component'], inplace=True)
        ax = tic.unstack().plot(kind='bar',
                                rot=0,
                                color=([colors.get(key)
                                        for key in
                                        ['egoblue1',
                                         'egoblue2']]),
                                legend=False)
        ax.set_ylabel("Overnight costs of simulation")
        ax.set_title("Total costs of simulation, "
                     "voltage level and component", y=1.08)

    else:
        tic = costs_df[['component',
                        'capital_cost',
                        'voltage_level']]
        tic.set_index(['voltage_level', 'component'], inplace=True)
        ax = tic.unstack().plot(kind='bar',
                                rot=0,
                                color=([colors.get(key)
                                        for key in
                                        ['egoblue1',
                                         'egoblue2']]),
                                legend=False)
        ax.set_ylabel("Annualized costs per simulation periods")
        ax.set_title("Annualized costs per simulation periods, "
                     "voltage level and component", y=1.08)

    ax.set_xlabel('Voltage level and component')
    ax.set_yscale("log")
    ax.legend(('Grid', 'Storage'))
    ax.autoscale()

    if display is True:
        plt.show()
    else:
        fig = ax.get_figure()
        fig.set_size_inches(10, 8, forward=True)
        fig.savefig(filename,  dpi=100)
        plt.close()


def power_price_plot(ego, filename, display):
    """
    Plot power price of calculated scenario of timesteps and carrier

    Parameters
    ----------
    ego :class:`ego.io.eGo`

    Returns
    -------
    plot :obj:`matplotlib.pyplot.show`
            https://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.show
    """
    plt.rcdefaults()
    colors = ego_colore()
    fig, ax = plt.subplots()

    # plot power_price
    prc = ego.etrago.generator['power_price']
    bar_width = 0.35
    opacity = 0.4

    ind = np.arange(len(prc.index))    # the x locations for the groups
    width = 0.35       # the width of the bars: can also be len(x) sequence

    ax.barh(ind, prc, align='center', color=colors['egoblue1'])
    ax.set_yticks(ind)
    ax.set_yticklabels(prc.index)
    ax.invert_yaxis()

    ax.set_xlabel('Power price in €/MWh')
    ax.set_title('Power Costs per Carrier')

    ax.autoscale(tight=True)

    if display is True:
        plt.show()
    else:
        fig = ax.get_figure()
        fig.set_size_inches(10, 8, forward=True)
        fig.savefig(filename,  dpi=100)


def plot_storage_use(ego, filename, display):
    """Plot storage use by charge and discharge values

    Parameters
    ----------
    ego :class:`ego.io.eGo`

    Returns
    -------
    plot :obj:`matplotlib.pyplot.show`
            https://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.show
    """
    colors = ego_colore()

    ax = ego.etrago.\
        storage_charges[['charge', 'discharge']].plot(kind='bar',
                                                      title="Storage usage",
                                                      stacked=True,
                                                      color=([colors.get(key)
                                                              for key in
                                                              ['egoblue1',
                                                               'egoblue2']]),
                                                      figsize=(
                                                          15, 10),
                                                      legend=True,
                                                      fontsize=12)
    ax.set_xlabel("Kind of Storage", fontsize=12)
    ax.set_ylabel("Charge and Discharge in MWh", fontsize=12)
    ax.autoscale(tight=False)

    if display is True:
        plt.show()
    else:
        fig = ax.get_figure()
        fig.set_size_inches(10, 8, forward=True)
        fig.subplots_adjust(bottom=0.25)
        fig.savefig(filename,  dpi=100)


def get_country(session, region=None):
    """Get Geometries of scenario Countries
    """

    if region is None:
        # Define regions 'FR',
        region = ['DE', 'DK',  'BE', 'LU',
                  'NO', 'PL', 'CH', 'CZ', 'SE', 'NL']
    else:
        region
    # get database tabel
    query = session.query(RenpassGisParameterRegion.gid,
                          RenpassGisParameterRegion.stat_level,
                          RenpassGisParameterRegion.u_region_id,
                          RenpassGisParameterRegion.geom,
                          RenpassGisParameterRegion.geom_point)
    # get regions by query and filter
    Regions = [(gid, u_region_id, stat_level,
                shape.to_shape(geom),
                shape.to_shape(geom_point)) for gid, u_region_id, stat_level,
               geom, geom_point in query.filter(
               RenpassGisParameterRegion.u_region_id.
               in_(region)).all()]
    # define SRID
    crs = {'init': 'epsg:4326'}

    country = gpd.GeoDataFrame(
        Regions,  columns=['gid', 'stat_level', 'u_region_id',
                           'geometry', 'point_geom'], crs=crs)

    return country


def prepareGD(session, subst_id=None, version=None):
    """ Get MV grid districts for plotting
    """

    if version:

        query = session.query(EgoDpMvGriddistrict.subst_id,
                              EgoDpMvGriddistrict.geom)

        if isinstance(subst_id, list):
            Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
                       query.filter(EgoDpMvGriddistrict.version == version,
                                    EgoDpMvGriddistrict.subst_id.in_(
                                        subst_id)).all()]

        elif subst_id == "all":

            Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
                       query.filter(EgoDpMvGriddistrict.version ==
                                    version).all()]
        else:
            # ToDo query doesn't looks stable
            Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
                       query.filter(EgoDpMvGriddistrict.version ==
                                    version).all()]
    # toDo add values of sub_id etc. to popup
    else:
        # from model_draft

        query = session.query(EgoGridMvGriddistrict.subst_id,
                              EgoGridMvGriddistrict.geom)
        Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
                   query.filter(EgoGridMvGriddistrict.subst_id.in_(
                       subst_id)).all()]

    crs = {'init': 'epsg:3035'}
    region = gpd.GeoDataFrame(
        Regions, columns=['subst_id', 'geometry'], crs=crs)
    region = region.to_crs({'init': 'epsg:4326'})
    return region


def plot_edisgo_cluster(ego, filename, region=['DE'], display=False, dpi=600):
    """Plot the Clustering of selected Dingo networks

    Parameters
    ----------
    ego :class:`ego.io.eGo`
        self class object of eGo()
    filename: str
        file name for plot ``cluster_plot.pdf``
    region: list
        List of background countries e.g. ['DE', 'DK']
    display: boolean
        True show plot false print plot as ``filename``

    Returns
    -------
    plot :obj:`matplotlib.pyplot.show`
            https://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.show

    """
    session = ego.session
    version = ego.json_file['eTraGo']['gridversion']
    # get cluster
    cluster = ego.edisgo.grid_choice
    cluster = cluster.rename(columns={"the_selected_network_id": "subst_id"})
    cluster_id = list(cluster.subst_id)

    # get country Polygon
    cnty = get_country(session, region=region)
    # get grid districts singel
    if ego.json_file['eGo']['eDisGo'] is True:
        gridcluster = prepareGD(session, cluster_id, version)
        gridcluster = gridcluster.merge(cluster, on='subst_id')
        # get represented grids
        repre_grids = pd.DataFrame(columns=['subst_id',
                                            'geometry',
                                            'cluster_id',
                                            'style'])
        for cluster in gridcluster.index:

            rep_id = gridcluster.represented_grids[cluster]
            # represented_grids
            repre_grid = prepareGD(session, rep_id, version)
            repre_grid['cluster_id'] = gridcluster.subst_id[cluster]

            repre_grids = repre_grids.append(repre_grid, ignore_index=True)
        # add common SRID
        crs = {'init': 'epsg:4326'}
        repre_grids = gpd.GeoDataFrame(repre_grids, crs=crs)

    # get all MV grids
    bus_id = "all"
    mvgrids = prepareGD(session, bus_id, version)

    # start plotting
    figsize = 5, 5
    fig, ax = plt.subplots(1, 1, figsize=(figsize))

    cnty.plot(ax=ax, color='white',
              edgecolor='whitesmoke', alpha=0.5, linewidth=0.1)
    mvgrids.plot(ax=ax, color='white', alpha=0.1,  linewidth=0.1)
    if ego.json_file['eGo']['eDisGo'] is True:
        repre_grids.plot(ax=ax, column='cluster_id',
                         cmap='GnBu', edgecolor='whitesmoke',
                         linewidth=0.1,
                         legend=True)
        gridcluster.plot(ax=ax, column='no_of_points_per_cluster',
                         cmap='OrRd',
                         linewidth=0.1,
                         legend=True)

    # add storage distribution
    _storage_distribution(ego.etrago.network, scaling=1, filename=None,
                          ax=ax, fig=fig)
    ax.set_title('Grid district Clustering by Number of represent Grids')

    ax.autoscale(tight=True)

    if display is True:
        plt.show()
    else:
        fig = ax.get_figure()
        fig.set_size_inches(10, 8, forward=True)
        fig.savefig(filename,  dpi=dpi)
        plt.close()


def igeoplot(ego, tiles=None, geoloc=None, args=None):
    """Plot function in order to display eGo results on leaflet OSM map.
    This function will open the results in your main web browser

    Parameters
    ----------

    network_etrago:: class: `etrago.tools.io.NetworkScenario`
      eTraGo network object compiled by: meth: `etrago.appl.etrago`
    tiles: str
      Folium background map style `None` as OSM or `Nasa`
    geoloc: : obj: `list`
      Listwhich define center of map as (lon, lat)

    Returns
    -------
    plot: html
      HTML file with .js plot
     """

    #     # TODO
    #     # - use cluster or boxes to limit data volumn
    #     # - add Legend
    #     # - Map see: http://nbviewer.jupyter.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e

    network = ego.etrago.network
    session = ego.session
    # get scenario name from args
    scn_name = ego.json_file['eTraGo']['scn_name']
    version = ego.json_file['eTraGo']['gridversion']
    # define SRID
    crs = {'init': 'epsg:4326'}

    if geoloc is None:
        geoloc = [network.buses.y.mean(), network.buses.x.mean()]

    mp = folium.Map(tiles=None, location=geoloc,
                    control_scale=True, zoom_start=6)

    # add Nasa light background
    if tiles == 'Nasa':
        tiles = ("https://map1.vis.earthdata.nasa.gov/wmts-webmerc/" +
                 "VIIRS_CityLights_2012/default/GoogleMapsCompatible_" +
                 "Level8/{z}/{y}/{x}.jpg")
        attr = ('&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>')

        folium.raster_layers.TileLayer(tiles=tiles, attr=attr).add_to(mp)
    else:
        folium.raster_layers.TileLayer('OpenStreetMap').add_to(mp)
    # 'Stamen Toner'  OpenStreetMap

    # Legend name
    bus_group = folium.FeatureGroup(name='Buses full informations')
    # add buses

    for name, row in network.buses.iterrows():
        # get information of buses
        popup = """ <b> Bus: </b> {} <br>
     					Scenario: {} <br>
                        Carrier: {} <br>
     					Control: {} <br>
     					type: {} <br>
     					v_nom: {} <br>
     					v_mag_pu_set: {} <br>
     					v_mag_pu_min: {} <br>
     					v_mag_pu_max: {} <br>
     					sub_network: {} <br>
     					Version: {} <br>
     				""".format(row.name, scn_name, row['carrier'],
                    row['control'], row['type'], row['v_nom'],
                    row['v_mag_pu_set'],
                    row['v_mag_pu_min'], row['v_mag_pu_max'],
                    row['sub_network'], version)
        # add Popup values use HTML for formating
        folium.Marker([row["y"], row["x"]], popup=popup).add_to(bus_group)

    def convert_to_hex(rgba_color):
        """Convert rgba colors to hex
        """
        red = str(hex(int(rgba_color[0]*255)))[2:].capitalize()
        green = str(hex(int(rgba_color[1]*255)))[2:].capitalize()
        blue = str(hex(int(rgba_color[2]*255)))[2:].capitalize()

        if blue == '0':
            blue = '00'
        if red == '0':
            red = '00'
        if green == '0':
            green = '00'

        return '#' + red + green + blue

    # Prepare lines
    line_group = folium.FeatureGroup(name='Lines full informations')

    # get line Coordinates
    x0 = network.lines.bus0.map(network.buses.x)
    x1 = network.lines.bus1.map(network.buses.x)

    y0 = network.lines.bus0.map(network.buses.y)
    y1 = network.lines.bus1.map(network.buses.y)

    # get content
    lines = network.lines
    cols = list(network.lines.columns)

    # color map lines
    colormap = cm.linear.YlOrRd_09.scale(
        lines.s_nom.min(), lines.s_nom.max()).to_step(6)

    # add parameter
    for line in network.lines.index:
        popup = """ <b>Line:</b> {} <br>
                    version: {} <br>""".format(line, version)
        for col in cols:
            popup += """ {}: {} <br>""".format(col, lines[col][line])

        # change colore function
        l_color = colormapper_lines(
            colormap, lines, line, column="s_nom")
        # ToDo make it more generic
        folium.PolyLine(([y0[line], x0[line]], [y1[line], x1[line]]),
                        popup=popup, color=convert_to_hex(l_color)).\
            add_to(line_group)

    # Add results
    # add expansion costs per line
    lines = network.lines
    if 'network' in ego.json_file['eTraGo']['extendable']:
        lines['s_nom_expansion'] = lines.s_nom_opt.subtract(
            lines.s_nom, axis='index')
        lines['capital_investment'] = lines.s_nom_expansion.multiply(
            lines.capital_cost, axis='index')
    else:
        lines['s_nom_expansion'] = 0.
        lines['capital_investment'] = 0.

    # Prepare lines
    line_results_group = folium.FeatureGroup(name='Lines specific results')

    # color map lines
    colormap2 = cm.linear.YlOrRd_09.scale(
        lines.s_nom_expansion.min(), lines.s_nom_expansion.max()).to_step(6)

    # add parameter
    for line in network.lines.index:
        popup = """<b>Line:</b> {} <br>
            version: {} <br>
            capital_cost: {} <br>
            s_nom expansion: {} <br>
            investment: {} <br>
            length: {} <br>
            s_nom: {} <br>
            s_nom_extendable: {} <br>
            s_nom_max: {} <br>
            s_nom_min: {} <br>
            s_nom_opt: {} <br>
            type: {} <br>
            v_nom: {} <br>
            """.format(line, version,
                       lines.capital_cost[line],
                       lines.s_nom_expansion[line],
                       lines.capital_investment[line],
                       lines.length[line],
                       lines.s_nom[line],
                       lines.s_nom_extendable[line],
                       lines.s_nom_max[line],
                       lines.s_nom_min[line],
                       lines.s_nom_opt[line],
                       lines.type[line],
                       lines.v_nom[line])

        # change colore function
        lr_color = colormapper_lines(
            colormap2, lines, line, column="s_nom_expansion")
        # ToDo make it more generic
        folium.PolyLine(([y0[line], x0[line]], [y1[line], x1[line]]),
                        popup=popup,
                        color=convert_to_hex(lr_color)
                        ).add_to(line_results_group)

    # add grid districs
    if ego.json_file['eGo']['eDisGo'] is True:

        grid_group = folium.FeatureGroup(name='Grid district')
        # list(network.buses.index) # change to selected grids

        subst_id = list(ego.edisgo.grid_choice.the_selected_network_id)
        district = prepareGD(session, subst_id, version)

        # todo does not work with k-mean Cluster
        # Add for loop
        crs = {'init': 'epsg:4326'}

        # for name, row in district.iterrows():
        pop = """<b>Grid district:</b> {} <br>
            """.format('Number')

        folium.GeoJson(district).add_to(grid_group).add_child(folium.Popup(pop))

        # Add cluster grids
        repgrid_group = folium.FeatureGroup(name='represented Grids by Cluster')
        cluster = ego.edisgo.grid_choice
        cluster = cluster.rename(
            columns={"the_selected_network_id": "subst_id"})

        repre_grids = pd.DataFrame(columns=['subst_id',
                                            'geometry',
                                            'cluster_id'
                                            'color',
                                            'mpl_color'])

        style_function = (lambda x: {
                          'fillColor':  x['properties']['color'],
                          'weight': 0.5, 'color': 'black'})

        for idx in cluster.index:

            pop2 = """<b>Represented Grid:</b> {} <br>
                """.format(cluster.subst_id[idx])

            cluster_id = list(cluster.represented_grids[idx])
            # represented_grids
            repre_grid = prepareGD(session, cluster_id, version)
            repre_grid['cluster_id'] = cluster.subst_id[idx]

            repre_grids = repre_grids.append(repre_grid, ignore_index=True)
            # prepare cluster colore
            vals = list(repre_grids.cluster_id)  # cluster_id
            normal = mpl.colors.Normalize(vals)
            # cm.get_cmap('BrBG')
            cellColours = plt.cm.jet(vals)  # change here colormap
            repre_grids['color'] = ''

            for i in repre_grids.index:
                repre_grids['mpl_color'][i] = cellColours[i]
                # get hex color
                repre_grids['color'][i] = convert_to_hex(
                    repre_grids['mpl_color'][i])

            repre_grids['mpl_color'] = ''

            repre_grids = gpd.GeoDataFrame(
                repre_grids, geometry='geometry', crs=crs)

            folium.GeoJson(repre_grids,
                           style_function=style_function
                           ).add_to(repgrid_group).add_child(
                folium.Popup(pop2))

    # Create storage expantion plot
    store_group = folium.FeatureGroup(name='Storage expantion')

    sto_x = network.storage_units.bus.map(network.buses.x)
    sto_y = network.storage_units.bus.map(network.buses.y)
    cols = list(network.storage_units.columns)
    stores = network.storage_units
    sto_max = stores.p_nom_opt.max()

    for store in network.storage_units.index:
        popup = """ <b>Storage:</b> {} <br>
                    version: {} <br>""".format(store, version)
        for col in cols:
            popup += """ {}: {} <br>""".format(col, stores[col][store])

        # get storage radius by p_nom_opt
        if (stores['p_nom_opt'][store] - stores['p_nom'][store]) > 0.:
            radius = (9**(1+stores['p_nom_opt'][store]/sto_max))
        if (stores['p_nom_opt'][store] - stores['p_nom'][store]) == 0.:
            radius = 0

        # add singel storage
        folium.CircleMarker(
            location=([sto_y[store], sto_x[store]]),
            radius=radius,
            popup=popup,
            color='#3186cc',
            fill=True,
            fill_color='#3186cc',
            weight=1
        ).add_to(store_group)

    # add layers and others
    colormap.caption = 'Colormap of Lines s_nom'
    colormap2.caption = 'Colormap of Lines investment'
    mp.add_child(colormap)
    mp.add_child(colormap2)

    # Add layer groups
    bus_group.add_to(mp)
    line_group.add_to(mp)
    if ego.json_file['eGo']['eDisGo'] is True:
        grid_group.add_to(mp)
        repgrid_group.add_to(mp)
    line_results_group.add_to(mp)
    store_group.add_to(mp)
    folium.LayerControl().add_to(mp)

    plugins.Fullscreen(
        position='topright',
        title='Fullscreen',
        title_cancel='Exit me',
        force_separate_button=True).add_to(mp)

    # Save Map
    html_dir = 'results/html'
    if not os.path.exists(log_dir):
        os.makedirs(html_dir)
    mp.save("results/html/iplot_map.html")

    # Display htm result from consol
    new = 2  # open in a new tab, if possible
    # open a public URL, in this case, the webbrowser docs
    path = os.getcwd()
    url = "results/html/iplot_map.html"
    webbrowser.open(url, new=new)


def colormapper_lines(colormap, lines, line, column="s_nom"):
    """ Colore Map for lines
    """
    # TODO Update and correct mapper
    l_color = []
    if colormap.index[6] >= lines[column][line] > colormap.index[5]:
        l_color = colormap.colors[5]
    elif colormap.index[5] >= lines[column][line] > colormap.index[4]:
        l_color = colormap.colors[4]
    elif colormap.index[4] >= lines[column][line] > colormap.index[3]:
        l_color = colormap.colors[3]
    elif colormap.index[3] >= lines[column][line] > colormap.index[2]:
        l_color = colormap.colors[2]
    elif colormap.index[2] >= lines[column][line] > colormap.index[1]:
        l_color = colormap.colors[1]
    elif colormap.index[1] >= lines[column][line] >= colormap.index[0]:
        l_color = colormap.colors[0]
    else:
        l_color = (0., 0., 0., 1.)
    return l_color


def _storage_distribution(network, ax, fig, scaling=1, filename=None):
    """
    Plot storage distribution as circles on grid nodes
    Displays storage size and distribution in network.
    Parameters
    ----------
    network : PyPSA network container
        Holds topology of grid including results from powerflow analysis
    filename : str
        Specify filename
        If not given, figure will be show directly
    """

    stores = network.storage_units
    storage_distribution = network.storage_units.p_nom_opt[stores.index]\
        .groupby(network.storage_units.bus)\
        .sum().reindex(network.buses.index, fill_value=0.)

    msd_max = storage_distribution.max()
    msd_median = storage_distribution[storage_distribution != 0].median()
    msd_min = storage_distribution[storage_distribution > 1].min()

    if msd_max != 0:
        LabelVal = int(log10(msd_max))
    else:
        LabelVal = 0
    if LabelVal < 0:
        LabelUnit = 'kW'
        msd_max, msd_median, msd_min = msd_max * \
            1000, msd_median * 1000, msd_min * 1000
        storage_distribution = storage_distribution * 1000
    elif LabelVal < 3:
        LabelUnit = 'MW'
    else:
        LabelUnit = 'GW'
        msd_max, msd_median, msd_min = msd_max / \
            1000, msd_median / 1000, msd_min / 1000
        storage_distribution = storage_distribution / 1000

    if sum(storage_distribution) == 0:
        network.plot(bus_sizes=0, ax=ax)
    else:
        network.plot(
            bus_sizes=storage_distribution * scaling,
            ax=ax,
            line_widths=0.3
        )
