eGo Tutorials
-------------




## Installation 


### eDisGo

### eTraGo 

The python tool eTraGo can be used in several forms like from a terminal as an execution program, by integrated development environments (IDE) like [Spyder](https://anaconda.org/anaconda/spyder),  [Jupyter notebooks](http://jupyter.org/install) or many more.

A description how you to install and work with eTraGo can be found [here](http://etrago.readthedocs.io/en/latest/getting_started.html).


### Notebook installation

Having Python 3 installed?  As eGo is designed as a Python package it is mandatory to have Python 3 installed. For this Tutorial we recommend to use an [virtual environment](https://virtualenv.pypa.io/en/stable/installation/). 
See this [tutorial](https://docs.python.org/3/tutorial/venv.html). 

If you already have a Python 3 environment you can follow this steps in your terminal:


```desktop

$ virtualenv ego_tutorial --clear -p python3.5
$ cd ego_tutorial
$ source bin/activate

$ pip3 install etrago==0.5.1
$ pip3 install -e git+https://github.com/openego/PyPSA.git@dev#egg=PyPSA

$ python3 -m pip install --upgrade pip
$ python3 -m pip install jupyter

```

### Start you Notebook

```desktop
$ jupyter notebook
```

See for more information [how to run your jupyter notebook](https://jupyter.readthedocs.io/en/latest/running.html#running).



<h4 style="color:Tomato;">Warning:</h4>
For using this Notebook you need an oedb access or a database dump of the input data. <br>
<h4 style="color:black;">Note:</h4>
The installation is only tested on Ubuntu 16.4. and Windows 10 with [Anaconda](https://www.anaconda.com/download/)

## Import eTraGo packages

We are importing the [main function](https://github.com/openego/eTraGo/blob/dev/etrago/appl.py) of eTraGo and its database and plotting functions. 


