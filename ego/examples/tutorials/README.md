# eGo Tutorials


## eDisGo
The python package eDisGo provides a toolbox for analysis and optimization of distribution grids. This software lives in the context of the research project open_eGo. It is closely related to the python project Ding0 as this project is currently the single data source for eDisGo providing synthetic grid data for whole Germany.


Learn more about:
*  [eDisGo – Optimization of flexibility options and grid expansion for distribution grids based on PyPSA](http://edisgo.readthedocs.io/en/dev/start_page.html)


## eTraGo
Optimization of flexibility options for transmission grids based on PyPSA.

A speciality in this context is that transmission grids are described by the 380, 220 and 110 kV in Germany. Conventionally the 110kV grid is part of the distribution grid. The integration of the transmission and ‘upper’ distribution grid is part of eTraGo.

The focus of optimization are flexibility options with a special focus on energy storages and grid expansion measures.


The python tool eTraGo can be used in several forms like from a terminal as an execution program, by integrated development environments (IDE) like [Spyder](https://anaconda.org/anaconda/spyder),  [Jupyter notebooks](http://jupyter.org/install) or many more.

A general description how you to install and work with eTraGo can be found also [here](http://etrago.readthedocs.io/en/latest/getting_started.html).


# Notebook installation

#### with Anaconda

Download and install your Python 3.x version of Anaconda [here](https://www.anaconda.com/download/). The full Documentation can be found [on this page.](https://docs.anaconda.com/anaconda/install/)

We use Anaconda with an own environment in order to reduze problems with Packages and different versions on our system. Learn more about [Anacona environments](https://conda.io/docs/user-guide/tasks/manage-environments.html). Remove your environment with _'conda env remove -n openMod_Zuerich2018'_.




##### Quick start - steps to do:

0. Sign-in on [openenergy-platform.org](http://openenergy-platform.org/login/)
1. Install Anacanda
2. Get eGo Repository from github
3. Create environment
4. Activate your environment
5. Install you notebook requirements
6. Make few settings for your notebook
7. Start your notebook and check if the notebook is running



##### Get eGo Repository and install it with an environment
```desktop

$ git clone -b features/tutorial https://git@github.com/openego/eGo.git
$ cd eGo/ego/examples/tutorials/
$ conda  env create --file requirements.yml
```

##### Activate your environment and run your notebooks
```desktop

$ source activate openMod_Zuerich2018
$ jupyter notebook
$ source deactivate
```

##### fixes and work arounds:

* Error in function plot_stacked_gen() due to data name changes. Fix error in  ../eGo/ego/examples/tutorials/src/etrago/etrago/tools/plot.py and  add: 'wind_offshore':'skyblue', 'wind_onshore':'skyblue', instead of 'wind';  restart kernel
plot_stacked_gen(network, resolution="MW")


##### API and ego.io settings

Your API settings will be saved in the folder .egoio in the file config.ini.


```desktop
[oedb]
dialect  = oedialect
username = <username>
database = oedb
host     = openenergy-platform.org
port     = 80
password = <token>
```


### Start you Notebook

```desktop
$ jupyter notebook
```

See for more information [how to run your jupyter notebook](https://jupyter.readthedocs.io/en/latest/running.html#running).


<h4 style="color:black;">Note:</h4>

The installation is only tested on Ubuntu 16.4. and Windows 10 with  [Anaconda](https://www.anaconda.com/download/)
