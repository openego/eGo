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

"""Graph helper functions, which are attached to network and sub_network
"""

# Functions which will be attached to network and sub_network

import scipy as sp, scipy.sparse
import numpy as np

from .descriptors import OrderedGraph

def graph(network, branch_components=None, weight=None):
    """Build networkx graph."""
    from . import components

    if isinstance(network, components.Network):
        if branch_components is None:
            branch_components = components.branch_components
        buses_i = network.buses.index
    elif isinstance(network, components.SubNetwork):
        if branch_components is None:
            branch_components = components.passive_branch_components
        buses_i = network.buses_i()
    else:
        raise TypeError("build_graph must be called with a Network or a SubNetwork")

    graph = OrderedGraph()

    # add nodes first, in case there are isolated buses not connected with branches
    graph.add_nodes_from(buses_i)

    # Multigraph uses the branch type and name as key
    def gen_edges():
        for c in network.iterate_components(branch_components):
            for branch in c.df.loc[slice(None) if c.ind is None
                                               else c.ind].itertuples():
                if weight is None:
                    data = {}
                else:
                    data = dict(weight=getattr(branch, weight))
                    if np.isinf(data['weight']): continue

                yield (branch.bus0, branch.bus1, (c.name, branch.Index), data)

    graph.add_edges_from(gen_edges())

    return graph

def adjacency_matrix(network, branch_components=None, busorder=None, weights=None):
    """
    Construct a sparse adjacency matrix (directed)

    Parameters
    ----------
    branch_components : iterable sublist of `branch_components`
       Buses connected by any of the selected branches are adjacent
       (default: branch_components (network) or passive_branch_components (sub_network))
    busorder : pd.Index subset of network.buses.index
       Basis to use for the matrix representation of the adjacency matrix
       (default: buses.index (network) or buses_i() (sub_network))
    weights : pd.Series or None (default)
       If given must provide a weight for each branch, multi-indexed
       on branch_component name and branch name.

    Returns
    -------
    adjacency_matrix : sp.sparse.coo_matrix
       Directed adjacency matrix
    """
    from . import components

    if isinstance(network, components.Network):
        if branch_components is None:
            branch_components = components.branch_components
        if busorder is None:
            busorder = network.buses.index
    elif isinstance(network, components.SubNetwork):
        if branch_components is None:
            branch_components = components.passive_branch_components
        if busorder is None:
            busorder = network.buses_i()
    else:
        raise TypeError(" must be called with a Network or a SubNetwork")

    no_buses = len(busorder)
    no_branches = 0
    bus0_inds = []
    bus1_inds = []
    weight_vals = []
    for c in network.iterate_components(branch_components):
        if c.ind is None:
            sel = slice(None)
            no_branches = len(c.df)
        else:
            sel = t.ind
            no_branches = len(c.ind)
        bus0_inds.append(busorder.get_indexer(c.df.loc[sel, "bus0"]))
        bus1_inds.append(busorder.get_indexer(c.df.loc[sel, "bus1"]))
        weight_vals.append(np.ones(no_branches)
                           if weights is None
                           else weights[c.name][sel].values)

    if no_branches == 0:
        return sp.sparse.coo_matrix((no_buses, no_buses))

    bus0_inds = np.concatenate(bus0_inds)
    bus1_inds = np.concatenate(bus1_inds)
    weight_vals = np.concatenate(weight_vals)

    return sp.sparse.coo_matrix((weight_vals, (bus0_inds, bus1_inds)),
                                shape=(no_buses, no_buses))

def incidence_matrix(network, branch_components=None, busorder=None):
    """
    Construct a sparse incidence matrix (directed)

    Parameters
    ----------
    branch_components : iterable sublist of `branch_components`
       Buses connected by any of the selected branches are adjacent
       (default: branch_components (network) or passive_branch_components (sub_network))
    busorder : pd.Index subset of network.buses.index
       Basis to use for the matrix representation of the adjacency matrix
       (default: buses.index (network) or buses_i() (sub_network))

    Returns
    -------
    incidence_matrix : sp.sparse.csr_matrix
       Directed incidence matrix
    """
    from . import components

    if isinstance(network, components.Network):
        if branch_components is None:
            branch_components = components.branch_components
        if busorder is None:
            busorder = network.buses.index
    elif isinstance(network, components.SubNetwork):
        if branch_components is None:
            branch_components = components.passive_branch_components
        if busorder is None:
            busorder = network.buses_i()
    else:
        raise TypeError(" must be called with a Network or a SubNetwork")

    no_buses = len(busorder)
    no_branches = 0
    bus0_inds = []
    bus1_inds = []
    for c in network.iterate_components(branch_components):
        if c.ind is None:
            sel = slice(None)
            no_branches += len(c.df)
        else:
            sel = c.ind
            no_branches += len(c.ind)
        bus0_inds.append(busorder.get_indexer(c.df.loc[sel, "bus0"]))
        bus1_inds.append(busorder.get_indexer(c.df.loc[sel, "bus1"]))
    bus0_inds = np.concatenate(bus0_inds)
    bus1_inds = np.concatenate(bus1_inds)

    return sp.sparse.csr_matrix((np.r_[np.ones(no_branches), -np.ones(no_branches)],
                                 (np.r_[bus0_inds, bus1_inds], np.r_[:no_branches, :no_branches])),
                                (no_buses, no_branches))
