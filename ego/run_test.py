from datetime import datetime
from tools.io import eGo
import sys
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput


def main():
    graphviz = GraphvizOutput()
    graphviz.output_file = 'basic.png'
    date = str(datetime.now())
    print(date)
    with PyCallGraph(output=graphviz):

        ego = eGo(jsonpath='scenario_setting_solver_option.json')

        print(ego.etrago.storage_charges)

        print(ego.etrago.storage_investment_costs)
        ego.etrago.storage_investment_costs.to_csv(
            date+'__etrago_storage_costs.csv')
        print(ego.etrago.grid_investment_costs)
        ego.etrago.grid_investment_costs.to_csv(date+'__etrago_grid_costs.csv')
        # test eTraGo plot and functions

        print(ego.edisgo.grid_investment_costs)
        ego.edisgo.grid_investment_costs.to_csv(date+'__edisgo_gridscosts.csv')

        ego.etrago_line_loading()
        ego.etrago_stacked_gen()
        ego.etrago_gen_dist()
        ego.etrago_storage_distribution()
        ego.etrago_voltage()

        # object size
        print(sys.getsizeof(ego))

    print(str(datetime.now()))


if __name__ == '__main__':
    main()
