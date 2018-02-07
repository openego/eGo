"""
Module to collect useful functions for writing results of eGo


ToDo:
	create resulte folder
	add plots
	write results to database
"""
import io
import pandas as pd
import os


def total_storage_charges(network, plot=False):
	"""
	Sum up the pysical storage values of the total scenario

	Parameters
	----------
	network (pypsa.network):
		PyPSA Network object modified by eTraGo

	plot (bool):
		Use plot function


	Results
	-------

	charge:
		Quantity of charged Energy in MWh over scenario time steps

	discharge:
		Quantity of discharged Energy in MWh over scenario time steps

	count:
		Number of storage units

	p_nom_o_sum:
		Sum of optimal installed power capacity
	"""

	charge =    network.storage_units_t.p[network.storage_units_t.\
						p[network.storage_units[network.storage_units.\
						p_nom_opt>0].index].values>0.].\
						groupby(network.storage_units.carrier, axis=1).sum().sum()

	discharge = network.storage_units_t.p[network.storage_units_t.\
						p[network.storage_units[network.storage_units.\
						p_nom_opt>0].index].values<0.].\
						groupby(network.storage_units.carrier, axis=1).sum().sum()


	count =     network.storage_units.bus[network.storage_units.\
						p_nom_opt>0].count()

	p_nom_o_sum = network.storage_units.p_nom_opt.groupby(network.storage_units.\
														carrier, axis=0).sum()

	results = pd.concat([charge.rename('charge'), discharge.rename('discharge'),
	                   p_nom_o_sum],axis=1, join='outer')

	if plot:
		import matplotlib.pyplot as plt
		ax = results[['charge','discharge']].plot(kind='bar',
												  title ="Storage use",
												  stacked=True,
												  #table=True,
												  figsize=(15, 10),
												  legend=True,
												  fontsize=12)
		ax.set_xlabel("MWh", fontsize=12)
		ax.set_ylabel("Storages", fontsize=12)
		plt.show()

	return results
