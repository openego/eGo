# -*- coding: utf-8 -*-
from datetime import datetime
from tools.io import eGo
import sys
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from pycallgraph import Config
import pandas as pd
import matplotlib.pyplot as plt
import os
from tools.utilities import define_logging
logger = define_logging(name='ego')


def ego_testing(ego):
    """ Call and test all ego Funktion
    """
    # full networks
    try:
        ego.etrago.network
        ego.etrago.disaggregated_network
        # aggregated results
        ego.etrago.storage_investment_costs
        ego.etrago.storage_charges
        ego.etrago.operating_costs
        ego.etrago.generator
        ego.etrago.grid_investment_costs
        # eTraGo functions
        ego.etrago.plot_line_loading()
        ego.etrago.plot_stacked_gen()
        ego.etrago.plot_curtailment()
        ego.etrago.plot_gen_dist()
        ego.etrago.plot_storage_distribution(scaling=1, filename=None)
        ego.etrago.plot_full_load_hours()
        # ego.etrago.plot_line_loading_diff(networkB=)  # Error
        ego.etrago.plot_plot_residual_load()  # Error
        ego.etrago.plot_voltage()  # Error
        ego.etrago.plot_nodal_gen_dispatch()
    except:
        logger.info("eTraGo failed testing")

    # eDisGo
    try:
        ego.edisgo
        ego.edisgo.network
        ego.edisgo.grid_investment_costs
        ego.edisgo.grid_choice
        ego.edisgo.successfull_grids
    except:
        logger.info("eDisGo failed testing")

    # eGo

    ego.total_investment_costs
    ego.total_operation_costs

    # ego plot  functions
    ego.plot_total_investment_costs(
        filename="results/plot_total_investment_costs.pdf")
    ego.plot_power_price(filename="results/plot_power_price.pdf")
    ego.plot_storage_usage(filename="results/plot_storage_usage.pdf")

    ego.iplot
    ego.plot_edisgo_cluster(filename="results/plot_edisgo_cluster.pdf")
    ego.plot_line_expansion(column='investment_costs',
                            filename="results/investment_costs.pdf")
    ego.plot_line_expansion(column='overnight_costs',
                            filename="results/overnight_costs.pdf")
    ego.plot_line_expansion(column='s_nom_expansion',
                            filename="results/s_nom_expansion.pdf")
    ego.plot_storage_expansion(column='overnight_costs',
                               filename="results/storage_capital_investment.pdf")


def main():
    logger.info('Start calculation')
    graphviz = GraphvizOutput()
    date = str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

    graphviz.output_file = 'results/'+str(date)+'_basic_process_plot.png'
    logger.info("Time: {} ".format(date))

    with PyCallGraph(output=graphviz, config=Config(groups=True)):

        ego = eGo(jsonpath='scenario_setting_local.json')
        logger.info('Start testing')
        ego_testing(ego)

        # object size
        logger.info("eGo object size: {} ".format(sys.getsizeof(ego)))

    logger.info("Time: {} ".format(str(datetime.now())))


if __name__ == '__main__':
    main()
