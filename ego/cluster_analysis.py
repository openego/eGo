import pandas as pd
import os
import numpy as np
import math


def concatenate_results(parameters, root_dir, grid_list,
                        dir_pattern='ding0_grid_{}'):
    """
    Takes all the results specified by `parameters` for all grids specified by
    `grid_list` and puts them into one dataframe.

    """

    # helper functions

    def _one_grid_results(dir):
        """
        Paths to results files. `dir` is the base directory were all results of
        all grids are saved.

        """

        powerflow_results_dir = os.path.join(dir, 'powerflow_results')
        grid_expansion_results_dir = os.path.join(dir,
                                                  'grid_expansion_results')

        results = {
            'v_mag_pu': os.path.join(powerflow_results_dir, 'voltages_pu.csv'),
            'current': os.path.join(powerflow_results_dir, 'currents.csv'),
            'active_power': os.path.join(
                powerflow_results_dir, 'active_powers.csv'),
            'reactive_power': os.path.join(
                powerflow_results_dir, 'reactive_powers.csv'),
            'apparent_power': os.path.join(
                powerflow_results_dir, 'apparent_powers.csv'),
            'grid_losses': os.path.join(
                powerflow_results_dir, 'grid_losses.csv'),
            'equipment_changes': os.path.join(
                grid_expansion_results_dir, 'equipment_changes.csv'),
            'grid_expansion_costs': os.path.join(
                grid_expansion_results_dir, 'grid_expansion_costs.csv'),
            'unresolved_issues': os.path.join(
                grid_expansion_results_dir, 'unresolved_issues.csv')
        }
        return results

    def _process_grid_expansion_costs(df):
        df.set_index(['grid_id', 'component'], drop=True, inplace=True)
        return df

    def _process_grid_losses(df):
        df.set_index(['grid_id', 'date'], drop=True, inplace=True)
        return df

    def _process_active_power(df):
        df.set_index(['grid_id', 'date'], drop=True, inplace=True)
        df = df[df.columns[[_.startswith('MVStation') for _ in df.columns]]]
        df = df.rename(columns={col: col.split('_')[0] for col in df.columns})
        return df

    # helper dicts

    unnamed_rename = {'grid_losses': {'Unnamed: 0': 'date'},
                      'grid_expansion_costs': {'Unnamed: 0': 'component'},
                      'active_power': {'Unnamed: 0': 'date'},
                      'reactive_power': {'Unnamed: 0': 'date'}}

    process_dict = {'grid_expansion_costs': _process_grid_expansion_costs,
                    'grid_losses': _process_grid_losses,
                    'active_power': _process_active_power,
                    'reactive_power': _process_active_power}

    # actual code

    results_lists = {p: [] for p in parameters}
    for grid_id in grid_list:
        dir = os.path.join(root_dir, dir_pattern.format(grid_id))
        if os.path.isdir(dir):
            tmp_results = _one_grid_results(dir)
            for param in parameters:
                res_df = pd.read_csv(tmp_results[param])
                res_df['grid_id'] = grid_id
                res_df.rename(columns=unnamed_rename[param], inplace=True)
                res_df = process_dict[param](res_df)
                results_lists[param].append(res_df)
        else:
            print("Directory {} does not exist.".format(dir))

    return {k: pd.concat(v) for k, v in results_lists.items()}


def key_figures_grids(results, cluster_info=None):

    # Grid reinforcement cost for each cluster
    key_figures = \
        results.groupby(
            ['grid_id', 'voltage_level']).sum()['total_costs'].unstack(
            'voltage_level').fillna(0).add_prefix('reinforcement_costs_')
    key_figures['reinforcement_costs_total'] = results.groupby(
        ['grid_id']).sum()['total_costs']

    if cluster_info is not None:
        # index cluster_info by grid id
        cluster_info = cluster_info.set_index(
            'the_selected_network_id', drop=True)

        # Scale grid reinforcement costs with cluster representativeness factor
        key_figures = pd.concat([key_figures, key_figures[[
            'reinforcement_costs_' + _ for _ in
            ['lv', 'mv/lv', 'mv', 'total']]].add_suffix('_scaled').mul(
            cluster_info['no_of_points_per_cluster'], axis=0)], axis=1)

        print(key_figures)
        extrapol = True
        if extrapol == True:
            key_figures['no_reprs'] = cluster_info['no_of_points_per_cluster']
            
            good_reprs = key_figures[
                    np.isfinite(key_figures['reinforcement_costs_total_scaled'])
                    ]['no_reprs'].sum()
            
            good_costs = key_figures[
                    np.isfinite(key_figures['reinforcement_costs_total_scaled'])
                    ]['reinforcement_costs_total_scaled'].sum()
            
            mean_good_costs = good_costs / good_reprs
            
            for idx, row in key_figures.iterrows():
                no_reprs = row['no_reprs']
                print(no_reprs)
                costs = row['reinforcement_costs_total_scaled']
                print(costs)
                if math.isnan(costs):
                    key_figures.at[
                            idx, 'reinforcement_costs_total_scaled'
                            ] = 0. #mean_good_costs * no_reprs
        
    return key_figures


if __name__ == '__main__':

    # INPUTS

    # main directory where all results are safed
    root_dir = '/home/student/Git/eGo/ego'

    # file with installed capacities etc. needed for clustering for each grid
    attr_file = os.path.join(root_dir, 'attributes.csv')

    # directory where summarized results and cluster results are safed
    out_dir = os.path.join(root_dir, 'ding0_grids_all')

    # specify file name of file containing grid expansion costs of each grid
    # if it does not exist it is created
    grid_expansion_results_file = os.path.join(
        out_dir, 'grid_expansion_costs.csv')

    # specify cluster file from ego clustering to project grid expansion costs
    # for the cluster; if no file is given all grids are used 
    cluster_sizes = range(10,1800,5)
    cluster_files = []
    for cs in cluster_sizes:
        cluster_files.append(
            os.path.join(
                    root_dir, 
                    'cluster_results/{}/grid_choice.csv'.format(cs)))

    # INPUTS end

    os.makedirs(out_dir, exist_ok=True)

    def _setup_cluster_key_figures(grid_expansion_results_file, attr_file,
                                   cluster_size, cluster_info, grid_list):
        # create or load grid expansion results file
        if os.path.isfile(grid_expansion_results_file):
            results = pd.read_csv(grid_expansion_results_file,
                                  index_col=[0, 1])
            results = results.sort_index()
            results = results.loc[pd.IndexSlice[grid_list, :], :]
        else:
            results = concatenate_results(
                ['grid_expansion_costs'], root_dir, grid_list)[
                'grid_expansion_costs']
            results.to_csv(os.path.join(out_dir, 'grid_expansion_costs.csv'))

        # key_figures contain grid expansion costs per voltage level and in
        # case a cluster file is given the scaled expansion costs per voltage
        # level and cluster
        key_figures = key_figures_grids(results, cluster_info=cluster_info)
        if cluster_size != 0:
            filename = os.path.join(
                out_dir, 'key_figures_cluster_{}.csv'.format(cluster_size))
        else:
            filename = os.path.join(out_dir, 'key_figures.csv')
        key_figures.to_csv(filename, index_label='grid_id')

        # Extract attributes for cluster
        attributes = pd.read_csv(attr_file, index_col='id').drop(
            'Unnamed: 0', axis=1)
        if cluster_size != 0:
            filename = os.path.join(
                out_dir, 'cluster_attributes_{}.csv'.format(cluster_size))
        else:
            filename = os.path.join(out_dir, 'cluster_attributes.csv')
        attributes_filtered = attributes.loc[grid_list]
        attributes_filtered.to_csv(filename, index_label='id')


    if cluster_files:
        for i in range(len(cluster_files)):
            cluster_file = cluster_files[i]
            cluster_size = cluster_sizes[i]
            cluster_info = pd.read_csv(cluster_file)
            grid_list = cluster_info['the_selected_network_id'].tolist()
            _setup_cluster_key_figures(grid_expansion_results_file, attr_file,
                                       cluster_size, cluster_info, grid_list)
    else:
        cluster_info = None
        grid_list = list(range(1, 3609))
        cluster_size = 0
        _setup_cluster_key_figures(grid_expansion_results_file, attr_file,
                                   cluster_size, cluster_info, grid_list)






