import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
import os
import seaborn as sns
import datetime
import geopandas

sns.set_style("ticks")


def load_results(path, cluster_size):
    if cluster_size is not None:
        key_figures = pd.read_csv(
            os.path.join(path, 'key_figures_cluster_{}.csv'.format(
                cluster_size)),
            index_col='grid_id')
    else:
        key_figures = pd.read_csv(
            os.path.join(path, 'key_figures.csv'),index_col='grid_id')
    return key_figures


def load_errors(path):
    edisgo_errors = pd.read_csv(os.path.join(path, 'grid_issues.csv'), index_col=[0])
    max_iter_error = edisgo_errors.loc[edisgo_errors['msg'].str.startswith("{")]
    max_iter_error.loc[:, 'msg'] = "Max. Iteration error"
    no_dingo_file = edisgo_errors.loc[
        edisgo_errors['msg'].str.startswith("[Errno 2]")]
    no_dingo_file.loc[:, 'msg'] = "No ding0 file"
    cum_cap = edisgo_errors.loc[
        edisgo_errors['msg'].str.startswith("ValueError('Cum")]
    cum_cap.loc[:, 'msg'] = "Cumulative capacity differs"
    remaing_errors = edisgo_errors[~edisgo_errors.index.isin(
        list(max_iter_error.index) + list(no_dingo_file.index) + list(cum_cap.index))].replace(
        {"ValueError('Power flow analysis did not converge.',)": 'Not converged'})

    return pd.concat([remaing_errors.reset_index().groupby('msg').agg('count'),
                      max_iter_error.reset_index().groupby('msg').agg('count'),
                      no_dingo_file.reset_index().groupby('msg').agg('count'),
                      cum_cap.reset_index().groupby('msg').agg('count')])


def grid_extension_costs(key_figures, cluster_size,
                         levels=True,
                         plot_path=os.path.abspath('.'),
                         aggregated=False):
    if levels:
        columns = ['reinforcement_costs_' + _ for _ in ['lv', 'mv/lv', 'mv']]
    else:
        raise NotImplementedError

    sns.set_context('talk')

    if aggregated:
        key_figures[columns].sum(axis=0).plot(
            kind='bar',
            stacked=False,
            colormap=ListedColormap(sns.color_palette("GnBu", 3)),
            linewidth=0)
    else:
        key_figures[columns].plot(kind='bar',
                                  stacked=True,
                                  colormap=ListedColormap(
                                      sns.color_palette("GnBu", 3)),
                                  linewidth=0)
    plt.xlabel('')
    plt.ylabel('Costs in k€')
    sns.despine(top=True, right=True, left=False, bottom=True)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_path, 'Grid_reinforcement_costs_{}.pdf'.format(cluster_size)))


def edisgo_errors(errors, plot_path=os.path.abspath('.')):

    sns.set_context('talk')
    errors.plot(kind='barh',
                colormap=ListedColormap(sns.color_palette("GnBu", 2)),
                linewidth=0, figsize=(20, 10))
    plt.xlabel('Occurrences')
    plt.ylabel('')
    sns.despine(top=True, right=True, left=False, bottom=True)
    plt.legend().remove()
    try:
        plt.tight_layout()
    except:
        pass
    plt.savefig(os.path.join(plot_path, 'edisGo_errors.pdf'))


def cluster_costs_approximation_diff(clusters_diff,
                                     plot_path=os.path.abspath('.'),
                                     cluster_sizes=[10]):
    
    plt_name = "Cluster Convergence"

    fig, ax = plt.subplots()
    fig.set_size_inches(15,9)
    
    clusters_diff.drop('Cluster All', inplace=True)
    
    xticks = cluster_sizes
    
    x = range(len(xticks))
    y = clusters_diff.values
    plt.plot(x, y, '*')
    
    plt.xticks(x[::8], xticks[::8], rotation=45, rotation_mode="anchor")

    plt.xlabel('Cluster size')
#    plt.xticks(rotation=0)
    plt.ylabel('Deviation from reinforcement costs')
    plt.grid()

    #plt.tight_layout()
    plt.savefig(os.path.join(plot_path, 'Grid_reinforcement_costs_diff.pdf'))


def cluster_costs_approximation(clusters, plot_path=os.path.abspath('.')):
    # Compare quality of grid extension cost estimation

    sns.set_context('talk')

    (clusters / 1e3).plot(kind='bar',
                  stacked=True,
                  colormap=ListedColormap(sns.color_palette("GnBu", 10)),
                  linewidth=0, figsize=(20, 12))
    plt.xlabel('')
    plt.xticks(rotation=0)
    plt.ylabel('Grid reinforcement costs in M€')

    sns.despine(top=True, right=True, left=True, bottom=True)

    #plt.tight_layout()
    plt.savefig(os.path.join(plot_path, 'Grid_reinforcement_costs_comparison.pdf'))


if __name__ == '__main__':

    root_dir = '/home/student/Git/eGo/ego'
    plot_path = os.path.join(root_dir, 'plots')
    os.makedirs(plot_path, exist_ok=True)
    folder = 'ding0_grids_all (cleaned)'

    cluster_sizes = range(10,1800,5)

    # # plot computable and non-computable grids for each cluster size
    # for cluster_size in cluster_sizes:
    #
    #     grid_issues = pd.read_csv(
    #             os.path.join(root_dir, 'grid_issues.csv'),
    #             index_col=[0])
    #     non_computable = grid_issues.index
    #
    #     grid_choice = pd.read_csv(
    #         os.path.join(root_dir, 'grid_choice_{}.csv'.format(cluster_size)),
    #         index_col=[2])
    #     grid_choice['represented_grids'] = grid_choice.apply(
    #         lambda x: eval(x['represented_grids']), axis=1)
    #
    #     dicti = {}
    #     for i in grid_choice.index:
    #         number_grids = grid_choice.loc[i, 'no_of_points_per_cluster']
    #         grid_list = grid_choice.loc[i, 'represented_grids']
    #         number_non_computable = 0
    #         for grid in grid_list:
    #             if grid in non_computable:
    #                 number_non_computable += 1
    #         dicti[i] = number_non_computable
    #     df = pd.DataFrame(dicti, index=['non_computable'])
    #     grid_choice['non_computable'] = df.T
    #     grid_choice['computable'] = grid_choice['no_of_points_per_cluster'] - \
    #                                 grid_choice['non_computable']
    #
    #     grid_choice.loc[:, ['non_computable', 'computable']].plot(kind='bar',
    #               stacked=True)
    #     plt.savefig(os.path.join(
    #         plot_path, 'grid_choice_{}_computable_grids.png'.format(
    #             cluster_size)))
    #     grid_choice.to_csv(
    #         os.path.join(
    #             root_dir, 'grid_choice_{}_computable_grids.csv'.format(
    #                 cluster_size)))

    key_figures = {}
    for cs in cluster_sizes:
        key_figures[cs] = load_results(
            os.path.join(root_dir, folder), cs)
    key_figuresAll = load_results(os.path.join(root_dir, folder),
                                  None)

    # # plot costs for grids in clusters
    # for cs in cluster_sizes:
    #     grid_extension_costs(key_figures[cs], cs, plot_path=plot_path)

#    # errors
#    edisgo_errors_df = load_errors(root_dir)
#    edisgo_errors(edisgo_errors_df, plot_path=plot_path)

    reinforce_costs_cols = ['reinforcement_costs_' + _ for _ in ['lv', 'mv/lv', 'mv']]
    reinforce_costs_cols_scaled = [_ + '_scaled' for _ in reinforce_costs_cols]
#  
    # hack scaled values for all grids
    for col in reinforce_costs_cols:
        ext_col = col + '_scaled'
        if ext_col not in key_figuresAll.columns:
            key_figuresAll = pd.concat([key_figuresAll, key_figuresAll[col].to_frame(col + '_scaled')], axis=1)
#    # end hack

    cluster = {}
    for cs in cluster_sizes:
        cluster[cs] = key_figures[cs]['reinforcement_costs_total_scaled'].sum()
#                reinforce_costs_cols_scaled].sum().T.to_frame(
#            'Cluster {}'.format(cs))
#        cluster[cs] = key_figures[cs][
#                reinforce_costs_cols_scaled].sum().T.to_frame(
#            'Cluster {}'.format(cs))
        
    cluster_all = key_figuresAll[reinforce_costs_cols_scaled].sum().T.to_frame(
        'Cluster All')  
    cluster_all = cluster_all * (3393 / (2677)) 
    
    real_val = cluster_all.sum()
    
    cluster_vals = pd.Series()
    for k, v in cluster.items():
#        cluster_all = cluster_all.join(v)
        ext = v/real_val
        cluster_vals.set_value(k, ext)
        cluster_vals.set_value('Cluster All', 1.)
        

    cluster_costs_approximation_diff(cluster_vals, plot_path, cluster_sizes)
    # cluster_costs_approximation(cluster_all.T, plot_path)
