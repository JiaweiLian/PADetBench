import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import random
from value2asr import value2asr


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='plot')
    parser.add_argument('--data-path', default='results/vehicle.csv', type=str, help='The path to the data')
    parser.add_argument('--save-path', default='results/vehicle.pdf', type=str, help='The path to save the plot')
    parser.add_argument('--l-axis', default='adv_type', type=str, help='The field name of legend')
    parser.add_argument('--n-axis', default='benchmark', type=str, help='The field name of n subplots')
    parser.add_argument('--x-axis', default='model_name', type=str, help='The field name of x axis')
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
        (data['benchmark'] == 'entire')
    ]

    # sort the data based on the adversarial type
    data = data.sort_values(by=['model_name'], ascending=True)

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
    y_tick_max = np.ceil(y_max * 10) * 10
    y_tick_min = np.floor(y_min * 10) * 10
    y_tick_num = int(y_tick_max - y_tick_min) // 10 + 1
    y_ticks = np.linspace(y_tick_min, y_tick_max, y_tick_num, dtype=int)

    # plot the data
    marker = ['.', 'o', 'v', '^', '<', '>', '1', '2', '3', '4', 's', 'p', 'P', '*', 'h', 'H', '+', 'x', 'X', 'D', 'd']
    cm = plt.get_cmap(random.choice(['tab20', 'tab20b', 'tab20c']))

    # set the figure size
    ax = plt.figure(figsize=(10, 3.8)).add_subplot(111)
    
    # draw the violin plot
    for field_x, data_x in data.groupby(args.x_axis):
        x = axis_ticklables[args.x_axis].index(field_x)
        ax.violinplot(data_x['ASR'], positions=[x], showmeans=True, showextrema=True, widths=1)

    # draw the scatter plot
    scatters = list()
    for ticklabel_l, data_l in data.groupby(args.l_axis):
        l = axis_ticklables[args.l_axis].index(ticklabel_l)
        xs = [axis_ticklables[args.x_axis].index(x) for x in data_l[args.x_axis]]
        scatter = ax.scatter(xs, y=data_l['ASR'], marker=marker[(l+1)%len(marker)], color=cm.colors[l%len(cm.colors)], label=ticklabel_l, s=30)
        scatters.append(scatter)
    
    # set y axis ticks and labels
    ax.set_yticks(y_ticks/100)
    ax.set_yticklabels(y_ticks, fontsize=8)
    ax.set_ylabel('ASR', fontsize=10)

    # set the x axis labels
    ax.set_xlabel(axis_name[args.x_axis], fontsize=10)
    ax.set_xticks(range(len(axis_ticklables[args.x_axis])))
    # set the x axis ticks and labels and rotate the labels
    ax.set_xticklabels(axis_ticklables[args.x_axis], fontsize=8, rotation=45, ha='right')
    ax.grid(True, linewidth=0.1)
    ax.tick_params(direction='in')

    # set the frame width of the plot
    for spine in plt.gca().spines.values():
        spine.set_linewidth(1)

    # setting the interval between the plots
    plt.subplots_adjust(wspace=0.2, hspace=1)
    
    # set the margin of the plot
    plt.tight_layout()

    # set the legend
    if len(scatters) <= 10: # for vehicle
        lgd = ax.legend(handles=scatters, loc='upper right', ncols=1, fontsize=8, frameon=True, edgecolor='black', fancybox=False, borderpad=0.5)
    else: # for walker
        lgd = ax.legend(handles=scatters, loc='upper right', ncols=5, fontsize=8, frameon=True, edgecolor='black', fancybox=False, borderpad=0.5, columnspacing=0)

    # save the plot to pdf
    plt.savefig(args.save_path, dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
    