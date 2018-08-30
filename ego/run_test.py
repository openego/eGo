from datetime import datetime
from tools.io import eGo
import sys
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from pycallgraph import Config
import pandas as pd
import matplotlib.pyplot as plt
import os


def main():
    graphviz = GraphvizOutput()
    date = str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    date
    graphviz.output_file = 'results/'+str(date)+'_basic_process_plot.png'
    print(date)
    with PyCallGraph(output=graphviz, config=Config(groups=True)):

        ego = eGo(jsonpath='scenario_setting.json')
        path = os.getcwd()
        file_prefix = path+'/results/'+str(date)

        # object size
        print(sys.getsizeof(ego))

    print(str(datetime.now()))


if __name__ == '__main__':
    main()
