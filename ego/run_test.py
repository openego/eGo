from datetime import datetime
from tools.io import eGo
import sys
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
import pandas as pd


def main():
    graphviz = GraphvizOutput()
    graphviz.output_file = 'basic.png'
    date = str(datetime.now())
    print(date)
    with PyCallGraph(output=graphviz):

        ego = eGo(jsonpath='scenario_setting.json')

        print(ego.etrago.storage_charges)
        pd.DataFrame(ego.etrago.storage_charges)\
            .to_csv(date+'__etrago_storage_charges.csv')
        print(ego.etrago.storage_investment_costs)

        pd.DataFrame(ego.etrago.storage_investment_costs)\
            .to_csv(date+'__etrago_storage_costs.csv')
        print(ego.etrago.grid_investment_costs)
        etg_gic = pd.DataFrame(ego.etrago.grid_investment_costs)
        etg_gic.to_csv(date+'__etrago_grid_costs.csv')
        # test eTraGo plot and functions

        print(ego.edisgo.grid_investment_costs)
        edg_gic = pd.DataFrame(ego.edisgo.grid_investment_costs)
        edg_gic.to_csv(date+'__edisgo_gridscosts.csv')

        ego.etrago_line_loading()
        ego.etrago_storage_distribution()
        ego.etrago_voltage()

        ego.plot_total_investment_cost()
        print(ego.total_investment_costs)
        ego_t = pd.DataFrame(ego.total_investment_costs)
        ego_t.to_csv(date+'__ego_total-costs.csv')

        ego.mv_grid_costd

        # object size
        print(sys.getsizeof(ego))

    print(str(datetime.now()))


if __name__ == '__main__':
    main()
