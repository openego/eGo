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

from etrago.tools.plot import (plot_line_loading, plot_stacked_gen,
                                     add_coordinates, curtailment, gen_dist,
                                     storage_distribution)

def make_all_plots(eTraGo_network):
	# make a line loading plot
	plot_line_loading(eTraGo_network)

	# plot stacked sum of nominal power for each generator type and timestep
	plot_stacked_gen(eTraGo_network, resolution="MW")

	# plot to show extendable storages
	storage_distribution(eTraGo_network)

	return
