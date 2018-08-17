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
# TODO  - Implement plotly for iplot

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
    # import geopandas as gpd
    import folium
    from folium import plugins
    import branca.colormap as cm
    import webbrowser
    from egoio.db_tables.model_draft import EgoGridMvGriddistrict
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


def grid_storage_investment(ego):
    """
    """
    colors = ego_colore()

    n_levels = len(ego._ehv_grid_costs.capital_cost)

    means_grid = ego._ehv_grid_costs.capital_cost

    means_storage = ego._storage_costs.capital_cost

    fig, ax = plt.subplots()

    index = np.arange(n_levels)
    bar_width = 0.35

    opacity = 0.4
    error_config = {'ecolor': '0.3'}

    rects1 = ax.bar(index, means_grid, bar_width,
                    alpha=opacity, color=colors['egoblue1'],
                    error_kw=error_config,
                    label='Grid expansion costs per annuity')

    rects2 = ax.bar(index + bar_width, means_storage, bar_width,
                    alpha=opacity, color=colors['egoblue4'],
                    error_kw=error_config,
                    label='Storage expansion costs per annuity')

    ax.set_xlabel('Voltage level')
    ax.set_ylabel('Annualized costs per time step')
    ax.set_title('Annualized costs per time step and component')
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(list(ego._ehv_grid_costs.voltage_level))
    ax.legend()

    fig.tight_layout()
    plt.show()


#
# def igeoplot(network, session, tiles=None, geoloc=None, args=None):
#     """Plot function in order to display eGo results on leaflet OSM map.
#     This function will open the results in your main Webbrowser
#
#     Parameters
#     ----------
#
#     network_etrago:: class: `etrago.tools.io.NetworkScenario`
#         eTraGo network object compiled by: meth: `etrago.appl.etrago`
#     tiles: str
#             Folium background map style `None` as OSM or `Nasa`
#     geoloc: : obj: `list`
#         List which define center of map as (lon, lat)
#
#     Returns
#     -------
#     plot: html
#         HTML file with .js plot
#     """
#     # TODO
#     # - implement eDisGo Polygons
#     # - fix version problems of data
#     # - use  grid.ego_dp_hvmv_substation subst_id and otg_id
#     # - use cluster or boxes to limit data volumn
#     # - add Legend
#     # - Map see: http://nbviewer.jupyter.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e
#     # - test cluster
#
#     if geoloc is None:
#         geoloc = [network.buses.y.mean(), network.buses.x.mean()]
#
#     mp = folium.Map(tiles=None, location=geoloc,
#                     control_scale=True, zoom_start=6)
#
#     # add Nasa light background
#     if tiles == 'Nasa':
#         tiles = 'https://map1.vis.earthdata.nasa.gov/wmts-webmerc/VIIRS_CityLights_2012/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg'
#         attr = ('&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>')
#
#         folium.raster_layers.TileLayer(tiles=tiles, attr=attr).add_to(mp)
#     else:
#         folium.raster_layers.TileLayer('OpenStreetMap').add_to(mp)
#         # 'Stamen Toner'  OpenStreetMap
#
#     # Legend name
#     bus_group = folium.FeatureGroup(name='Buses')
#     # add buses
#
#     # get scenario name from args
#     scn_name = args['eTraGo']['scn_name']
#     version = args['eTraGo']['gridversion']
#
#     for name, row in network.buses.iterrows():
#         popup = """ < b > Bus: < /b > {} < br >
# 					carrier: {} < br >
# 					control: {} < br >
# 					type: {} < br >
# 					v_nom: {} < br >
# 					v_mag_pu_set: {} < br >
# 					v_mag_pu_min: {} < br >
# 					v_mag_pu_max: {} < br >
# 					sub_network: {} < br >
# 					Scenario: {} < br >
# 					version: {} < br >
# 				""".format(row.name, scn_name, row['carrier'],
#                row['control'], row['type'], row['v_nom'], row['v_mag_pu_set'],
#                row['v_mag_pu_min'], row['v_mag_pu_max'], row['sub_network'], version)  # add Popup values use HTML for formating
#         folium.Marker([row["y"], row["x"]], popup=popup).add_to(bus_group)
#
#     # Prepare lines
#     line_group = folium.FeatureGroup(name='Lines')
#
#     # get line Coordinates
#     x0 = network.lines.bus0.map(network.buses.x)
#     x1 = network.lines.bus1.map(network.buses.x)
#
#     y0 = network.lines.bus0.map(network.buses.y)
#     y1 = network.lines.bus1.map(network.buses.y)
#
#     # get content
#     text = network.lines
#
#     # color map lines
#     colormap = cm.linear.Set1.scale(
#         text.s_nom.min(), text.s_nom.max()).to_step(6)
#
#     def convert_to_hex(rgba_color):
#         """
#         convert rgba colors to hex
#         """
#         red = str(hex(int(rgba_color[0]*255)))[2:].capitalize()
#         green = str(hex(int(rgba_color[1]*255)))[2:].capitalize()
#         blue = str(hex(int(rgba_color[2]*255)))[2:].capitalize()
#
#         if blue == '0':
#             blue = '00'
#         if red == '0':
#             red = '00'
#         if green == '0':
#             green = '00'
#
#         return '#' + red + green + blue
#
#     # toDo add more parameter
#     for line in network.lines.index:
#         popup = """ <b>Line:</b> {} <br>
# 					version: {} <br>
# 					v_nom: {} <br>
# 					s_nom: {} <br>
# 					capital_cost: {} <br>
# 					g: {} <br>
# 					g_pu: {} <br>
# 					terrain_factor: {} <br>
# 				""".format(line, version, text.v_nom[line],
#                text.s_nom[line], text.capital_cost[line],
#                text.g[line], text.g_pu[line],
#                text.terrain_factor[line]
#                )
#         # ToDo make it more generic
#
#         def colormaper():
#             l_color = []
#             if colormap.index[6] >= text.s_nom[line] > colormap.index[5]:
#                 l_color = colormap.colors[5]
#             elif colormap.index[5] >= text.s_nom[line] > colormap.index[4]:
#                 l_color = colormap.colors[4]
#             elif colormap.index[4] >= text.s_nom[line] > colormap.index[3]:
#                 l_color = colormap.colors[3]
#             elif colormap.index[3] >= text.s_nom[line] > colormap.index[2]:
#                 l_color = colormap.colors[2]
#             elif colormap.index[2] >= text.s_nom[line] > colormap.index[1]:
#                 l_color = colormap.colors[1]
#             elif colormap.index[1] >= text.s_nom[line] >= colormap.index[0]:
#                 l_color = colormap.colors[0]
#             else:
#                 l_color = (0., 0., 0., 1.)
#             return l_color
#
#         l_color = colormaper()
#
#         folium.PolyLine(([y0[line], x0[line]], [y1[line], x1[line]]),
#                         popup=popup, color=convert_to_hex(l_color)).\
#             add_to(line_group)
#
#     # add grod districs
#     grid_group = folium.FeatureGroup(name='Grid district')
#     subst_id = list(network.buses.index)
#     district = prepareGD(session, subst_id, version)
#     # todo does not work with k-mean Cluster
#     # folium.GeoJson(district).add_to(grid_group)
#
#     # add layers and others
#     colormap.caption = 'Colormap of Lines s_nom'
#     mp.add_child(colormap)
#
#     # Add layer groups
#     bus_group.add_to(mp)
#     line_group.add_to(mp)
#     grid_group.add_to(mp)
#     folium.LayerControl().add_to(mp)
#
#     plugins.Fullscreen(
#         position='topright',
#         title='Fullscreen',
#         title_cancel='Exit me',
#         force_separate_button=True).add_to(mp)
#
#     # Save Map
#     mp.save('map.html')
#
#     # Display htm result from consol
#     new = 2  # open in a new tab, if possible
#     # open a public URL, in this case, the webbrowser docs
#     path = os.getcwd()
#     url = path+"/map.html"
#     webbrowser.open(url, new=new)

# def prepareGD(session, subst_id=None, version=None):
#     """
#     """
#
#     if version == 'v0.2.11':
#         query = session.query(EgoDpMvGriddistrict.subst_id,
#                               EgoDpMvGriddistrict.geom)
#
#         Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
#                    query.filter(EgoDpMvGriddistrict.version == version,
#                                 EgoDpMvGriddistrict.subst_id.in_(subst_id)).all()]
#     # toDo add values of sub_id etc. to popup
#     else:
#         query = session.query(EgoGridMvGriddistrict.subst_id,
#                               EgoGridMvGriddistrict.geom)
#         Regions = [(subst_id, shape.to_shape(geom)) for subst_id, geom in
#                    query.all()]
#
#     region = pd.DataFrame(Regions, columns=['subst_id', 'geometry'])
#     crs = {'init': 'epsg:3035'}
#     region = gpd.GeoDataFrame(
#         Regions, columns=['subst_id', 'geometry'], crs=crs)
#
#     return region


def power_price_plot(ego):
    """
    plot power price of calculated scenario of timesteps and carrier

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

    return plt.show()


def plot_etrago_production(ego):
    """
    input eGo
    Bar plot all etrago costs
    """

    # fig = plt.figure(figsize=(18,10), dpi=1600)
    # plt.pie(ego.etrago['p'],autopct='%.1f')
    # plt.title('Procentage of power production')

    # max(ego.etrago['investment_costs'])/(1000*1000*1000) # T€/kW->M€/KW ->GW/MW

    # Chare of investment costs get volume
    # ego.etrago['investment_costs'].sum()/(1000*1000*1000)

    ego.etrago['p'].plot(kind="pie",
                         subplots=True,
                         figsize=(10, 10),
                         autopct='%.1f')

    plt.show()


def plotting_invest(result):
    """
    Dataframe input of eGo
    """
    fig, ax = plt.subplots()

    ax.set_ylabel('Costs in €')
    ax.set_title('Investment Cost')
    ax.set_xlabel('Investments')

    result.plot(kind='bar', ax=ax)

    return


def plot_storage_use(storages):
    """
    Intput ego.storages
    """

    ax = storages[['charge', 'discharge']].plot(kind='bar',
                                                title="Storage usage",
                                                stacked=True,
                                                # table=True,
                                                figsize=(
                                                    15, 10),
                                                legend=True,
                                                fontsize=12)
    ax.set_xlabel("Kind of Storage", fontsize=12)
    ax.set_ylabel("Charge and Discharge in MWh", fontsize=12)
    plt.show()
    return
