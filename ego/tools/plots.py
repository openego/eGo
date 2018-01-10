"""
Module to collect useful functions for plotting results of eGo

ToDo:
	histogram
	etc.
	Implement plotly
"""
__copyright__ = "tba"
__license__ = "tba"
__author__ = "tba"

import numpy as np
import pandas as pd
from etrago.tools.plot import (plot_line_loading, plot_stacked_gen,
                                     add_coordinates, curtailment, gen_dist,
				                     storage_distribution,
									 plot_voltage,plot_residual_load)
import folium
from folium import plugins
import branca.colormap as cm
import webbrowser

import pyproj as proj
from shapely.geometry import Polygon, Point, MultiPolygon
from geoalchemy2 import *
import geopandas as gpd

import logging
import os
logger = logging.getLogger(__name__)

def make_all_plots(network):
	# make a line loading plot
	plot_line_loading(network)

	# plot stacked sum of nominal power for each generator type and timestep
	plot_stacked_gen(network, resolution="MW")

	# plot to show extendable storages
	storage_distribution(network)

	plot_residual_load(network)

	plot_voltage(network)

	curtailment(network)

	gen_dist(network)


	return


#session = oedb_session(section='oedb')
#session.bind

#network = eTraGo


#igeoplot(network)


def igeoplot(network, session, tiles=None, geoloc=None):
	"""
	Plot function in order to display eGo results on leaflet OSM map.
	This function will open the results in your main Webbrowser

	Parameters
	----------

	network (PyPSA):
		PyPSA network container
	tiles (str):
		Folium background map style 'None' as OSM
		or 'Nasa'
	geoloc (list):
		Define center of map as (lon,lat)

	Results:
    --------
		HTML Plot page

	ToDos:
	------
	implement eDisGo Polygons
		fix version problems of data
		use  grid.ego_dp_hvmv_substation subst_id and otg_id

	use cluster or boxes to limit data volumn

	Legend
	Map
    http://nbviewer.jupyter.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e
	"""

	if geoloc is None:
		geoloc = [network.buses.y.mean(),network.buses.x.mean()]

	mp = folium.Map(tiles=None,location=geoloc, control_scale=True, zoom_start=6)

	# add Nasa light background
	if tiles == 'Nasa':
		tiles = 'https://map1.vis.earthdata.nasa.gov/wmts-webmerc/VIIRS_CityLights_2012/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg'
		attr = ('&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>')

		folium.raster_layers.TileLayer(tiles = tiles, attr=attr).add_to(mp)
	else:
		folium.raster_layers.TileLayer('OpenStreetMap').add_to(mp)
		# 'Stamen Toner'  OpenStreetMap

	# Legend name
	bus_group = folium.FeatureGroup(name='Buses')
	# add buses
	for name, row in network.buses.iterrows():
		popup = """ <b> Bus:</b> {} <br>
					carrier: {} <br>
					control: {} <br>
					type:{} <br>
					v_nom:{} <br>
					v_mag_pu_set:{} <br>
					v_mag_pu_min:{} <br>
					v_mag_pu_max:{} <br>
					sub_network:{} <br>
					Scenario: {} <br>
					version: {}  <br>
				""".format(row.name, row['scn_name'],row['carrier'],
				           row['control'],row['type'],row['v_nom'],row['v_mag_pu_set'],
						   row['v_mag_pu_min'],row['v_mag_pu_max'],row['sub_network']
						   ,row['scn_name'],row['version']) # add Popup values use HTML for formating
		folium.Marker([row["y"], row["x"]], popup=popup ).add_to(bus_group)

	# Prepare lines
	line_group = folium.FeatureGroup(name='Lines')

	# get line Coordinates
	x0 = network.lines.bus0.map(network.buses.x)
	x1 = network.lines.bus1.map(network.buses.x)

	y0 = network.lines.bus0.map(network.buses.y)
	y1 = network.lines.bus1.map(network.buses.y)

	# get content
	text = network.lines

	# color map lines
	colormap = cm.linear.Set1.scale(text.s_nom.min(), text.s_nom.max()).to_step(6)

	def convert_to_hex(rgba_color):
		"""
		convert rgba colors to hex
		"""
		red = str(hex(int(rgba_color[0]*255)))[2:].capitalize()
		green = str(hex(int(rgba_color[1]*255)))[2:].capitalize()
		blue = str(hex(int(rgba_color[2]*255)))[2:].capitalize()

		if blue=='0':
			blue = '00'
		if red=='0':
			red = '00'
		if green=='0':
			green='00'

		return '#'+ red + green + blue


	for line in network.lines.index:
		popup = """ <b>Line:</b> {} <br>
					version: {} <br>
					v_nom: {} <br>
					s_nom: {} <br>
					cables: {} <br>
					capital_cost: {} <br>
					frequency: {} <br>
					g: {} <br>
					g_pu: {} <br>
					terrain_factor: {} <br>
				""".format(line, text.version[line], text.v_nom[line],
				           text.s_nom[line], text.cables[line], text.capital_cost[line],
						   text.frequency[line],text.g[line],text.g_pu[line],
						   text.terrain_factor[line]
						   )
		# ToDo make it more generic
		def colormaper():
			l_color =[]
			if colormap.index[6] >= text.s_nom[line] > colormap.index[5]:
				l_color = colormap.colors[5]
			elif colormap.index[5] >= text.s_nom[line] > colormap.index[4]:
				l_color = colormap.colors[4]
			elif colormap.index[4] >= text.s_nom[line] > colormap.index[3]:
				l_color = colormap.colors[3]
			elif colormap.index[3] >= text.s_nom[line] > colormap.index[2]:
				l_color = colormap.colors[2]
			elif colormap.index[2] >= text.s_nom[line] > colormap.index[1]:
				l_color = colormap.colors[1]
			elif colormap.index[1] >= text.s_nom[line] >= colormap.index[0]:
				l_color = colormap.colors[0]
			else:
				l_color = (0.,0.,0.,1.)
			return l_color

		l_color =colormaper()

		folium.PolyLine(([y0[line], x0[line]], [y1[line], x1[line]]), popup=popup, color=convert_to_hex(l_color)).add_to(line_group)

	# add grod districs
	grid_group = folium.FeatureGroup(name='Grid district')
	subst_id = list(network.buses.index)
	version = 'v0.2.10' #'v0.2.11' #network.buses.version[1]
	district = prepareGD(session, subst_id , version)
	folium.GeoJson(district).add_to(grid_group)

	# add layers and others
	colormap.caption = 'Colormap of Lines s_nom'
	mp.add_child(colormap)

	# Add layer groups
	bus_group.add_to(mp)
	line_group.add_to(mp)
	grid_group.add_to(mp)
	folium.LayerControl().add_to(mp)

	plugins.Fullscreen(
    					position='topright',
    					title='Fullscreen',
    					title_cancel='Exit me',
    					force_separate_button=True).add_to(mp)


	# Save Map
	mp.save('map.html')

	# Display htm result from consol
	new = 2 # open in a new tab, if possible
	# open a public URL, in this case, the webbrowser docs
	path = os.getcwd()
	url = path+"/map.html"
	webbrowser.open(url,new=new)


def prepareGD(session, subst_id= None, version=None ):

	from egoio.db_tables.model_draft import EgoGridMvGriddistrict
	from egoio.db_tables.grid import EgoDpMvGriddistrict

	if version == 'v0.2.11':
		query = session.query(EgoDpMvGriddistrict.subst_id, EgoDpMvGriddistrict.geom)

		Regions = [(subst_id,shape.to_shape(geom)) for subst_id, geom in
				query.filter(EgoDpMvGriddistrict.version == version ,
				EgoDpMvGriddistrict.subst_id.in_(subst_id)).all()]
	else:
		query = session.query(EgoGridMvGriddistrict.subst_id, EgoGridMvGriddistrict.geom)
		Regions = [(subst_id,shape.to_shape(geom)) for subst_id, geom in
	            query.all()]


	region = pd.DataFrame(Regions, columns=['subst_id','geometry'])
	crs = {'init': 'epsg:3035'}
	region = gpd.GeoDataFrame(Regions, columns=['subst_id','geometry'],crs=crs)

	return region
