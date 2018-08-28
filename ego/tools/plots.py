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
if not 'READTHEDOCS' in os.environ:
    from etrago.tools.plot import (plot_line_loading, plot_stacked_gen,
                                   add_coordinates, curtailment, gen_dist,
                                   storage_distribution,
                                   plot_voltage, plot_residual_load)
    import pyproj as proj
    from shapely.geometry import Polygon, Point, MultiPolygon
    from geoalchemy2 import *
    import geopandas as gpd
    import folium
    from folium import plugins
    import branca.colormap as cm
    import webbrowser
    from egoio.db_tables.model_draft import (
        EgoGridMvGriddistrict, RenpassGisParameterRegion)
    from egoio.db_tables.grid import EgoDpMvGriddistrict
    import matplotlib.pyplot as plt

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
    """
    """
    colors = {'egoblue1': '#1F567D',
              'egoblue2': '#84A2B8',
              'egoblue3': '#A3B9C9',
              'egoblue4': '#C7D5DE'
              }

    return colors


def grid_storage_investment(ego, filename, display, var=None):
    """
    """
    colors = ego_colore()
    bar_width = 0.35
    opacity = 0.4

    if var == 'overnight_cost':
        tic = ego.total_investment_costs[['component',
                                          'overnight_costs', 'voltage_level']]
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
        tic = ego.total_investment_costs[['component',
                                          'capital_cost', 'voltage_level']]
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
               geom, geom_point in query.filter(RenpassGisParameterRegion.u_region_id.
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
                                    EgoDpMvGriddistrict.subst_id.in_(subst_id)).all()]

        elif subst_id == "all":

            Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
                       query.filter(EgoDpMvGriddistrict.version == version).all()]
        else:
            # ToDo query doesn't looks stable
            Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
                       query.filter(EgoDpMvGriddistrict.version == version).all()]
    # toDo add values of sub_id etc. to popup
    else:
        # from model_draft

        query = session.query(EgoGridMvGriddistrict.subst_id,
                              EgoGridMvGriddistrict.geom)
        Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
                   query.filter(EgoGridMvGriddistrict.subst_id.in_(subst_id)).all()]

    crs = {'init': 'epsg:3035'}
    region = gpd.GeoDataFrame(
        Regions, columns=['subst_id', 'geometry'], crs=crs)
    region = region.to_crs({'init': 'epsg:4326'})
    return region


def plot_edisgo_cluster(ego, filename, region=['DE'], display=False):
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
    cluster = ego.edisgo_networks.grid_choice
    cluster = cluster.rename(columns={"the_selected_network_id": "subst_id"})
    cluster_id = list(cluster.subst_id)

    # get country Polygon
    cnty = get_country(session, region=region)
    # get grid districts
    gridcluster = prepareGD(session, cluster_id, version)
    gridcluster = gridcluster.merge(cluster, on='subst_id')

    # get all MV grids
    bus_id = "all"
    mvgrids = prepareGD(session, bus_id, version)

    # start plotting
    figsize = 5, 5
    fig, ax = plt.subplots(1, 1, figsize=(figsize))

    cnty.plot(ax=ax, color='white', alpha=0.5)
    mvgrids.plot(ax=ax, color='white', alpha=0.1)
    gridcluster.plot(ax=ax, column='cluster_percentage',
                     cmap='OrRd', legend=True)

    ax.set_title('Grid district Clustering by weighting (%)')

    ax.autoscale(tight=True)

    if display is True:
        plt.show()
    else:
        fig = ax.get_figure()
        fig.set_size_inches(10, 8, forward=True)
        fig.savefig(filename,  dpi=100)


def igeoplot(ego, tiles=None, geoloc=None, args=None):
    """Plot function in order to display eGo results on leaflet OSM map.
    This function will open the results in your main Webbrowser

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
    #     # - implement eDisGo Polygons
    #     # - fix version problems of data
    #     # - use  grid.ego_dp_hvmv_substation subst_id and otg_id
    #     # - use cluster or boxes to limit data volumn
    #     # - add Legend
    #     # - Map see: http://nbviewer.jupyter.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e
    #     # - test cluster
    #     # - add logger

    network = ego.etrago_network
    session = ego.session

    if geoloc is None:
        geoloc = [network.buses.y.mean(), network.buses.x.mean()]

    mp = folium.Map(tiles=None, location=geoloc,
                    control_scale=True, zoom_start=6)

    # add Nasa light background
    # http://nbviewer.jupyter.org/github/ocefpaf/folium_notebooks/blob/master/test_add_tile_layer.ipynb
    if tiles == 'Nasa':
        tiles = 'https://map1.vis.earthdata.nasa.gov/wmts-webmerc/VIIRS_CityLights_2012/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg'
        attr = ('&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>')

        folium.raster_layers.TileLayer(tiles=tiles, attr=attr).add_to(mp)
    else:
        folium.raster_layers.TileLayer('OpenStreetMap').add_to(mp)
    # 'Stamen Toner'  OpenStreetMap

    # Legend name
    bus_group = folium.FeatureGroup(name='Buses full informations')
    # add buses

    # get scenario name from args
    scn_name = ego.json_file['eTraGo']['scn_name']
    version = ego.json_file['eTraGo']['gridversion']

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
                    row['control'], row['type'], row['v_nom'], row['v_mag_pu_set'],
                    row['v_mag_pu_min'], row['v_mag_pu_max'], row['sub_network'], version)
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

    # color map lines
    colormap = cm.linear.YlOrRd_09.scale(
        lines.s_nom.min(), lines.s_nom.max()).to_step(6)

    # add parameter
    for line in network.lines.index:
        popup = """<b>Line:</b> {} <br>
            version: {} <br>
            angle_diff: {} <br>
            b: {} <br>
            b_pu: {} <br>
            bus0: {} <br>
            bus1: {} <br>
            capital_cost: {} <br>
            g: {} <br>
            g_pu: {} <br>
            length: {} <br>
            num_parallel: {} <br>
            r: {} <br>
            r_pu: {} <br>
            s_nom: {} <br>
            s_nom_extendable: {} <br>
            s_nom_max: {} <br>
            s_nom_min: {} <br>
            s_nom_opt: {} <br>
            sub_network: {} <br>
            terrain_factor: {} <br>
            type: {} <br>
            v_ang_max: {} <br>
            v_ang_min: {} <br>
            v_nom: {} <br>
            x: {} <br>
            x_pu: {} <br>
            """.format(line, version,
                       lines.angle_diff[line],
                       lines.b[line],
                       lines.b_pu[line],
                       lines.bus0[line],
                       lines.bus1[line],
                       lines.capital_cost[line],
                       lines.g[line],
                       lines.g_pu[line],
                       lines.length[line],
                       lines.num_parallel[line],
                       lines.r[line],
                       lines.r_pu[line],
                       lines.s_nom[line],
                       lines.s_nom_extendable[line],
                       lines.s_nom_max[line],
                       lines.s_nom_min[line],
                       lines.s_nom_opt[line],
                       lines.sub_network[line],
                       lines.terrain_factor[line],
                       lines.type[line],
                       lines.v_ang_max[line],
                       lines.v_ang_min[line],
                       lines.v_nom[line],
                       lines.x[line],
                       lines.x_pu[line])

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
        lines['s_nom_expansion'] = 'No expansion calculated'
        lines['capital_investment'] = 'No investment calculated'

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
                        popup=popup, color=convert_to_hex(lr_color)).add_to(line_results_group)

    # add grid districs

    grid_group = folium.FeatureGroup(name='Grid district')
    # list(network.buses.index) # change to selected grids

    #
    subst_id = list(ego.edisgo_networks.grid_choice.the_selected_network_id)
    district = prepareGD(session, subst_id, version)
    print(district)
    # todo does not work with k-mean Cluster
    # Add for loop
    # crs = {'init': 'epsg:4326'}

    # for name, row in district.iterrows():
    pop = """<b>Grid district:</b> {} <br>
            """.format('12121212')

    # date = gpd.GeoDataFrame(row, columns=['subst_id', 'geometry'], crs=crs)

    folium.GeoJson(district).add_to(grid_group).add_child(folium.Popup(pop))

    # add layers and others
    colormap.caption = 'Colormap of Lines s_nom'
    colormap2.caption = 'Colormap of Lines investment'
    mp.add_child(colormap)
    mp.add_child(colormap2)

    # Add layer groups
    bus_group.add_to(mp)
    line_group.add_to(mp)
    grid_group.add_to(mp)
    line_results_group.add_to(mp)
    folium.LayerControl().add_to(mp)

    plugins.Fullscreen(
        position='topright',
        title='Fullscreen',
        title_cancel='Exit me',
        force_separate_button=True).add_to(mp)

    # Save Map
    mp.save("results/html/iplot_map.html")

    # Display htm result from consol
    # TODO add var inoder to control browser Display
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
