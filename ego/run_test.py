from datetime import datetime
from tools.io import eGo
import sys
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
import pandas as pd
import matplotlib.pyplot as plt


def main():
    graphviz = GraphvizOutput()
    graphviz.output_file = 'results/basic_process_plot.png'
    date = str(datetime.now())
    print(date)
    with PyCallGraph(output=graphviz):

        ego = eGo(jsonpath='scenario_setting.json')

        # Check eTraGo
        print("eTraGo container: %s", ego.etrago_network)
        print("eTraGo container (disaggregated): %s",
              ego.etrago_disaggregated_network)

        # Check eTraGo results
        print(ego.etrago.operating_costs)
        pd.DataFrame(ego.etrago.operating_costs)\
            .to_csv('results/'+date+'__etrago_operating_costs.csv')

        print(ego.etrago.storage_charges)
        pd.DataFrame(ego.etrago.storage_charges)\
            .to_csv('results/'+date+'__etrago_storage_charges.csv')
        print(ego.etrago.storage_investment_costs)

        pd.DataFrame(ego.etrago.storage_investment_costs)\
            .to_csv('results/'+date+'__etrago_storage_costs.csv')
        print(ego.etrago.grid_investment_costs)
        etg_gic = pd.DataFrame(ego.etrago.grid_investment_costs)
        etg_gic.to_csv('results/'+date+'__etrago_grid_costs.csv')

        # test eTraGo plot and functions
        try:
            a = ego.etrago_line_loading()
            a.savefig("results/etrago_line_loading.pdf", bbox_inches='tight')
        except:
            pass

        # eGo Results
        # ego.total_investment_costs
        print(ego.total_investment_costs)
        ego_t = pd.DataFrame(ego.total_investment_costs)
        ego_t.to_csv('results/'+date+'__ego_total-costs.csv')

        # eDisGo results
        try:
            print(ego.edisgo.grid_investment_costs)
            edg_gic = pd.DataFrame(ego.edisgo.grid_investment_costs)
            edg_gic.to_csv('results/'+date+'__edisgo_gridscosts.csv')
        except:
            pass

        # object size
        print(sys.getsizeof(ego))

    print(str(datetime.now()))


if __name__ == '__main__':
    main()
