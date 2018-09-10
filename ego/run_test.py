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
        logger.info("ego.etrago.network: {} ".format(ego.etrago.network))
        logger.info("ego.etrago.disaggregated_network: {} ".format(
            ego.etrago.disaggregated_network))

        # aggregated results
        logger.info("Testing of aggregated results ego.etrago. ")
        logger.info("storage_investment_costs: {} ".format(
            ego.etrago.storage_investment_costs))
        logger.info("storage_charges: {} ".format(
            ego.etrago.storage_charges))

        ego.etrago.operating_costs
        ego.etrago.generator
        ego.etrago.grid_investment_costs
        # eTraGo functions
        try:
            ego.etrago.plot_line_loading()
            ego.etrago.plot_stacked_gen()
            ego.etrago.plot_curtailment()
            ego.etrago.plot_gen_dist()
            ego.etrago.plot_storage_distribution(scaling=1, filename=None)
            ego.etrago.plot_full_load_hours()
            # ego.etrago.plot_line_loading_diff(networkB=)  # Error
            # ego.etrago.plot_plot_residual_load()  # Error
            # ego.etrago.plot_voltage()  # Error
            ego.etrago.plot_nodal_gen_dispatch()
        except:
            logger.info("eTraGo plotting failed testing")

    except:
        logger.info("eTraGo failed testing")
    # eDisGo
    try:
        logger.info("ego.edisgo: {} ".format(
            ego.edisgo))
    except:
        logger.info("ego.ego.edisgo failed testing")
    try:
        logger.info("ego.edisgo.network: {} ".format(
            ego.edisgo.network))
    except:
        logger.info("ego.edisgo.network failed testing")
    try:
        logger.info("ego.edisgo.grid_investment_costs: {} ".format(
            ego.edisgo.grid_investment_costs))
    except:
        logger.info("ego.edisgo.grid_investment_costs failed testing")
    try:
        logger.info("ego.edisgo.grid_choice: {} ".format(
            ego.edisgo.grid_choice))
    except:
        logger.info("ego.edisgo.grid_choice failed testing")
    try:
        logger.info("ego.edisgo.successfull_grids: {} ".format(
            ego.edisgo.successfull_grids))
    except:
        logger.info("ego.edisgo.successfull_grids failed testing")
    # eGo
    logger.info("ego.total_investment_costs: {} ".format(
        ego.total_investment_costs))
    logger.info("ego.total_operation_costs: {} ".format(
        ego.total_operation_costs))
    # ego plot  functions
    try:
        ego.plot_total_investment_costs(
            filename="results/plot_total_investment_costs.pdf")
    except:
        logger.info("ego.plot_total_investment_costs failed testing")
    try:
        ego.plot_power_price(filename="results/plot_power_price.pdf")
    except:
        logger.info("ego.plot_power_price failed testing")
    try:
        ego.plot_storage_usage(filename="results/plot_storage_usage.pdf")
    except:
        logger.info("ego.plot_storage_usage failed testing")
    try:
        ego.iplot
    except:
        logger.info("ego.iplot failed testing")
    try:
        ego.plot_edisgo_cluster(filename="results/plot_edisgo_cluster.pdf")
    except:
        logger.info(" plot_edisgo_cluster failed testing")
    try:
        ego.plot_line_expansion(column='investment_costs',
                                filename="results/investment_costs.pdf")
    except:
        logger.info(" plot_line_expansion failed testing")
    try:
        ego.plot_line_expansion(column='overnight_costs',
                                filename="results/overnight_costs.pdf")
    except:
        logger.info(" plot_line_expansion failed testing")
    try:
        ego.plot_line_expansion(column='s_nom_expansion',
                                filename="results/s_nom_expansion.pdf")
    except:
        logger.info(" plot_line_expansion failed testing")
    try:
        ego.plot_storage_expansion(column='overnight_costs',
                                   filename="results/storage_capital_investment.pdf")
    except:
        logger.info(" plot_storage_expansion failed testing")


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
