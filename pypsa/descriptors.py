

## Copyright 2015-2017 Tom Brown (FIAS), Jonas Hoersch (FIAS)

## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Descriptors for component attributes.
"""


# make the code as Python 3 compatible as possible
from __future__ import division
from __future__ import absolute_import
from six import iteritems, string_types


__author__ = "Tom Brown (FIAS), Jonas Hoersch (FIAS)"
__copyright__ = "Copyright 2015-2017 Tom Brown (FIAS), Jonas Hoersch (FIAS), GNU GPL 3"





#weak references are necessary to make sure the key-value pair are
#destroyed if the key object goes out of scope
from weakref import WeakKeyDictionary

from collections import OrderedDict

import networkx as nx
import pandas as pd
import numpy as np
import re

import inspect

import logging
logger = logging.getLogger(__name__)


from distutils.version import StrictVersion, LooseVersion
try:
    _nx_version = StrictVersion(nx.__version__)
except ValueError:
    _nx_version = LooseVersion(nx.__version__)

if _nx_version >= '1.12':
    class OrderedGraph(nx.MultiGraph):
        node_dict_factory = OrderedDict
        adjlist_dict_factory = OrderedDict
elif _nx_version >= '1.10':
    class OrderedGraph(nx.MultiGraph):
        node_dict_factory = OrderedDict
        adjlist_dict_factory = OrderedDict

        def __init__(self, data=None, **attr):
            self.node_dict_factory = ndf = self.node_dict_factory
            self.adjlist_dict_factory = self.adjlist_dict_factory
            self.edge_attr_dict_factory = self.edge_attr_dict_factory

            self.graph = {}   # dictionary for graph attributes
            self.node = ndf()  # empty node attribute dict
            self.adj = ndf()  # empty adjacency dict
            # attempt to load graph with data
            if data is not None:
                if isinstance(data, OrderedGraph):
                    try:
                        nx.convert.from_dict_of_dicts(
                            data.adj,
                            create_using=self,
                            multigraph_input=data.is_multigraph()
                        )
                        self.graph = data.graph.copy()
                        self.node.update((n,d.copy()) for n,d in data.node.items())
                    except:
                        raise nx.NetworkXError("Input is not a correct NetworkX graph.")
                else:
                    nx.convert.to_networkx_graph(data, create_using=self)
else:
    raise ImportError("NetworkX version {} is too old. At least 1.10 is needed.".format(nx.__version__))

class Dict(dict):
    """
    Dict is a subclass of dict, which allows you to get AND SET
    items in the dict using the attribute syntax!

    Stripped down from addict https://github.com/mewwts/addict/ .
    """

    def __setattr__(self, name, value):
        """
        setattr is called when the syntax a.b = 2 is used to set a value.
        """
        if hasattr(Dict, name):
            raise AttributeError("'Dict' object attribute "
                                 "'{0}' is read-only".format(name))
        else:
            self[name] = value

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError as e:
            raise AttributeError(e.args[0])

    def __delattr__(self, name):
        """
        Is invoked when del some_addict.b is called.
        """
        del self[name]

    _re_pattern = re.compile('[a-zA-Z_][a-zA-Z0-9_]*')

    def __dir__(self):
        """
        Return a list of object attributes.

        This includes key names of any dict entries, filtered to the
        subset of valid attribute names (e.g. alphanumeric strings
        beginning with a letter or underscore).  Also includes
        attributes of parent dict class.
        """
        dict_keys = []
        for k in self.keys():
            if isinstance(k, str):
                m = self._re_pattern.match(k)
                if m:
                    dict_keys.append(m.string)

        obj_attrs = list(dir(Dict))

        return dict_keys + obj_attrs


def get_switchable_as_dense(network, component, attr, snapshots=None, inds=None):
    """
    Return a Dataframe for a time-varying component attribute with values for all
    non-time-varying components filled in with the default values for the
    attribute.

    Parameters
    ----------
    network : pypsa.Network
    component : string
        Component object name, e.g. 'Generator' or 'Link'
    snapshots : pandas.Index
        Restrict to these snapshots rather than network.snapshots.
    inds : pandas.Index
        Restrict to these components rather than network.components.index

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> get_switchable_as_dense(network, 'Generator', 'p_max_pu')

"""

    df = network.df(component)
    pnl = network.pnl(component)

    index = df.index
    varying_i = pnl[attr].columns
    fixed_i = df.index.difference(varying_i)

    if inds is not None:
        index = index.intersection(inds)
        varying_i = varying_i.intersection(inds)
        fixed_i = fixed_i.intersection(inds)
    if snapshots is None:
        snapshots = network.snapshots
    return (pd.concat([
        pd.DataFrame(np.repeat([df.loc[fixed_i, attr].values], len(snapshots), axis=0),
                     index=snapshots, columns=fixed_i),
        pnl[attr].loc[snapshots, varying_i]
    ], axis=1).reindex(columns=index))


def allocate_series_dataframes(network, series):
    """
    Populate time-varying outputs with default values.

    Parameters
    ----------
    network : pypsa.Network
    series : dict
        Dictionary of components and their attributes to populate (see example)

    Returns
    -------
    None

    Examples
    --------
    >>> allocate_series_dataframes(network, {'Generator': ['p'],
                                             'Load': ['p']})

"""

    for component, attributes in iteritems(series):

        df = network.df(component)
        pnl = network.pnl(component)

        for attr in attributes:
            pnl[attr] = pnl[attr].reindex(columns=df.index,
                                          fill_value=network.components[component]["attrs"].at[attr,"default"])
