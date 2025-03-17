from cgitb import handler 
from turtle import color
import matplotlib
from matplotlib import legend, pyplot as plt
import numpy as np
import pandas as pd
import random
from scipy.interpolate import make_interp_spline
from scipy.interpolate import pchip
from value2asr import value2asr


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='plot')
    parser.add_argument('--data-path', default='results/walker.csv', type=str, help='The path to the data')
    parser.add_argument('--save-path', default='results/walker.pdf', type=str, help='The path to save the plot')
    parser.add_argument('--l-axis', default='model_name', type=str, help='The field name of legend')
    parser.add_argument('--n-axis', default='benchmark', type=str, help='The field name of n subplots')
    parser.add_argument('--x-axis', default='adv_type', type=str, help='The field name of x axis')
    parser.add_argument('--y-axis', default='mAR 50', type=str, help='The field name of y axis')

    args = parser.parse_args()

    matplotlib.rc('font',family='Times New Roman')

    axis_name = {
        'model_name': 'Model',
        'benchmark': 'Benchmark',
        'adv_type': 'Attack Method',
    }
    
    # read the data of given fields from the csv file
    data = pd.read_csv(args.data_path, usecols=['adv_type', 'benchmark', 'model_name', args.y_axis])

    # filter the data based on the benchmark
    data = data[
        (data['benchmark'] == 'entire') | (data['benchmark'] == 'weather') | (data['benchmark'] == 'distance') | (data['benchmark'] == 'sphere')
    ]

    # sort the data based on the adversarial type
    data = data.sort_values(by=['adv_type'], ascending=True)

    # changing the model name to the short name
    mapping_csv = pd.read_csv('results/mapping_model_name.csv')
    data['model_name'] = data['model_name'].map(dict(zip(mapping_csv['from'], mapping_csv['to'])))

    # mapping the adversarial type to the short name
    mapping_csv = pd.read_csv('results/mapping_adv_type.csv')
    data['adv_type'] = data['adv_type'].map(dict(zip(mapping_csv['from'], mapping_csv['to'])))

    # calculating ASR
    data = value2asr(data, args.y_axis)
    # filter the attack method
    data = data[data['adv_type'] != 'Clean']
    
    # get the number type of the n, x and y axis as well as the legend
    axis_ticklables = {
        args.n_axis: list(data[args.n_axis].unique()),
        args.l_axis: list(data[args.l_axis].unique()),
        args.x_axis: list(data[args.x_axis].unique()),
        args.y_axis: list(data[args.y_axis].unique()),
    }

    # get the maximum and minimum of the y axis
    y_max = data[args.y_axis].max()
    y_min = data[args.y_axis].min()

    # plot the data
    marker = ['.', 'o', 'v', '^', '<', '>', '1', '2', '3', '4', 's', 'p', 'P', '*', 'h', 'H', '+', 'x', 'X', 'D', 'd', '$\\clubsuit$', '$\\spadesuit$', '$\\heartsuit$']
    cm = plt.get_cmap(random.choice(['tab20', 'tab20b', 'tab20c']))

    # set the figure size
    fig, axs = plt.subplots(nrows=1, ncols=len(axis_ticklables[args.n_axis]), figsize=(18, 3))
    
    # set the frame width of the plot
    for spine in plt.gca().spines.values():
        spine.set_linewidth(1)
    
    # draw the violin plot
    for ticklabel_n, data_n in data.groupby(args.n_axis):
        n = axis_ticklables[args.n_axis].index(ticklabel_n)
        for ticklabel_x, data_nx in data_n.groupby(args.x_axis):
            x = axis_ticklables[args.x_axis].index(ticklabel_x)
            axs[n].violinplot(data_nx['ASR'], positions=[x], showmeans=True, showextrema=True, widths=1)
    
    # draw the scatter plot
    scatters = list()
    for ticklabel_n, data_n in data.groupby(args.n_axis):
        n = axis_ticklables[args.n_axis].index(ticklabel_n)
        for ticklabel_l, data_nl in data_n.groupby(args.l_axis):
            l = axis_ticklables[args.l_axis].index(ticklabel_l)
            xs = [axis_ticklables[args.x_axis].index(x) for x in data_nl[args.x_axis]]
            scatter = axs[n].scatter(x=xs, y=data_nl['ASR'], marker=marker[(l+1)%len(marker)], color=cm.colors[l%len(cm.colors)], label=ticklabel_l, s=30)
            if n == 0:
                scatters.append(scatter)

    # set the legend
    lgd = fig.legend(handles=scatters, loc='upper center', ncols=16, fontsize=8, frameon=True, edgecolor='black', fancybox=False, borderpad=0.5, bbox_to_anchor=(0.5, -0.))

    # set the x axis ticks and labels
    for n, ticklabel_n in enumerate(axis_ticklables[args.n_axis]):
        # set the title for each subplot and capitalize the first letter
        axs[n].set_title(ticklabel_n.capitalize(), fontsize=12, fontweight='bold')
        
        # set the x axis labels
        axs[n].set_xlabel(axis_name[args.x_axis], fontsize=10)
        axs[n].set_xticks(range(len(axis_ticklables[args.x_axis])))
        axs[n].set_xticklabels(axis_ticklables[args.x_axis], fontsize=8, rotation=45, ha='right')
        axs[n].grid(True, linewidth=0.1)
        axs[n].tick_params(direction='in')

        # set y axis ticks and labels
        y_tick_max = np.ceil(y_max * 10) * 10
        y_tick_min = np.floor(y_min * 10) * 10
        y_tick_num = int(y_tick_max - y_tick_min) // 10 + 1
        y_ticks = np.linspace(y_tick_min, y_tick_max, y_tick_num, dtype=int)
        axs[n].set_yticks(y_ticks/100)
        if n == 0:
            axs[n].set_yticklabels(y_ticks, fontsize=8)
            axs[n].set_ylabel('ASR', fontsize=10)
        else:
            # remove the y axis labels for the subplots except the first one
            axs[n].set_yticklabels([])

    # setting the interval between the plots
    plt.subplots_adjust(wspace=0.2, hspace=1)
    
    # set the margin of the plot
    plt.tight_layout()

    # save the plot to pdf
    plt.savefig(args.save_path, dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
    