from datetime import datetime
from tools.io import eGo
import sys
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
import pandas as pd
import matplotlib.pyplot as plt
import os


def main():
    graphviz = GraphvizOutput()
    date = str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    date
    graphviz.output_file = 'results/'+str(date)+'_basic_process_plot.png'
    print(date)
    with PyCallGraph(output=graphviz):

        ego = eGo(jsonpath='scenario_setting.json')
        path = os.getcwd()
        file_prefix = path+'/results/'+str(date)

        # Check eTraGo
        print("eTraGo container: %s", ego.etrago_network)
        print("eTraGo container (disaggregated): %s",
              ego.etrago_disaggregated_network)

        # Check eTraGo results
        print(ego.etrago.operating_costs)
        pd.DataFrame(ego.etrago.operating_costs)\
            .to_csv(file_prefix + '__etrago_operating_costs.csv')

        print(ego.etrago.storage_charges)
        pd.DataFrame(ego.etrago.storage_charges)\
            .to_csv(file_prefix + '__etrago_storage_charges.csv')
        print(ego.etrago.storage_investment_costs)

        pd.DataFrame(ego.etrago.storage_investment_costs)\
            .to_csv(file_prefix + '__etrago_storage_costs.csv')
        print(ego.etrago.grid_investment_costs)
        etg_gic = pd.DataFrame(ego.etrago.grid_investment_costs)
        etg_gic.to_csv(file_prefix + '__etrago_grid_costs.csv')

        # test eTraGo plot and functions
        try:
            a = ego.etrago_line_loading()
            a.savefig(file_prefix + "etrago_line_loading.pdf",
                      bbox_inches='tight')
        except:
            pass

        # eGo Results
        # ego.total_investment_costs
        print(ego.total_investment_costs)
        ego_t = pd.DataFrame(ego.total_investment_costs)
        ego_t.to_csv(file_prefix + '__ego_total-costs.csv')

        # eDisGo results
        try:
            print(ego.edisgo.grid_investment_costs)
            edg_gic = pd.DataFrame(ego.edisgo.grid_investment_costs)
            edg_gic.to_csv(file_prefix + '__edisgo_gridscosts.csv')
        except:
            pass

        # object size
        print(sys.getsizeof(ego))

    print(str(datetime.now()))


if __name__ == '__main__':
    main()
