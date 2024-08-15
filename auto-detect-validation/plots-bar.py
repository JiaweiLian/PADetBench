import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import random
from value2asr import value2asr

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='plot')
    parser.add_argument('--benchmark', default='entire', type=str, choices=['weather', 'distance', 'rotation-theta', 'rotation-phi', 'sphere', 'spot', 'entire'], help='Name of the benchmark')
    parser.add_argument('--data-path', default='results/vehicle.csv', type=str, help='The path to the data')
    parser.add_argument('--save-path', default='results/vehicle.pdf', type=str, help='The path to save the plot')
    parser.add_argument('--n-axis', default='model_name', type=str, help='The field name of n subplots')
    parser.add_argument('--x-axis', default='adv_type', type=str, help='The field name of x axis')
    parser.add_argument('--y-axis', default='mAR 50', type=str, help='The field name of y axis')

    args = parser.parse_args()
    
    matplotlib.rc('font',family='Times New Roman')

    # read the data of given fields from the csv file
    data = pd.read_csv(args.data_path, usecols=['benchmark', args.n_axis, args.x_axis, args.y_axis])

    # filter the data based on the benchmark
    data = data[data['benchmark'] == args.benchmark]

    # sort the data based on the adversarial type
    data = data.sort_values(by=[args.x_axis], ascending=True)

    # changing the model name to the short name
    mapping_csv = pd.read_csv(f'results/mapping_{args.n_axis}.csv')
    data[args.n_axis] = data[args.n_axis].map(dict(zip(mapping_csv['from'], mapping_csv['to'])))

    # mapping the adversarial type to the short name
    mapping_csv = pd.read_csv(f'results/mapping_{args.x_axis}.csv')
    data[args.x_axis] = data[args.x_axis].map(dict(zip(mapping_csv['from'], mapping_csv['to'])))

    # calculating ASR
    data = value2asr(data, args.y_axis)

    # get the number type of the n, x and y axis as well as the legend
    axis_ticklables = {
        args.n_axis: sorted(list(data[args.n_axis].unique())),
        args.x_axis: sorted(list(data[args.x_axis].unique())),
        args.y_axis: sorted(list(data[args.y_axis].unique()))
    }
    # list 'Clean' first in the adversarial type
    axis_ticklables[args.x_axis].remove('Clean')
    axis_ticklables[args.x_axis].insert(0, 'Clean')

    # plot the data
    columns = 12
    rows = int(np.ceil(len(axis_ticklables[args.n_axis]) / columns))
    fig, axss = plt.subplots(nrows=rows, ncols=columns, figsize=(12, 7))
    axs = axss.flatten()
    cm = plt.get_cmap(random.choice(['tab20', 'tab20b', 'tab20c']))

    for ticklabel_n, data_n in data.groupby(args.n_axis):
        n = axis_ticklables[args.n_axis].index(ticklabel_n)
        for ticklabel_x, data_nx in data_n.groupby(args.x_axis):
            x = axis_ticklables[args.x_axis].index(ticklabel_x)
            axs[n].barh(x, data_nx[args.y_axis], height=0.6, color=cm(x % 20), edgecolor='black', linewidth=0.5, alpha=0.3)

    for ticklabel_n, data_n in data.groupby(args.n_axis):
        n = axis_ticklables[args.n_axis].index(ticklabel_n)
        clean = data_n[data_n[args.x_axis] == 'Clean'][args.y_axis].values[0]
        for ticklabel_x, data_nx in data_n.groupby(args.x_axis):
            x = axis_ticklables[args.x_axis].index(ticklabel_x)
            axs[n].scatter(data_nx['ASR'], x, s=30, color=cm(x % 20), marker='P', edgecolor='white', linewidth=0.5)

    # set the title for each subplot
    for ticklabel_n, data_n in data.groupby(args.n_axis):
        n = axis_ticklables[args.n_axis].index(ticklabel_n)

        # set the frame width of each subplot
        for spine in axs[n].spines.values():
            spine.set_linewidth(0.5)
            
        # remove the y label for the subplots except the ones in the first column
        if n % columns != 0:
            axs[n].set_ylabel('')
            axs[n].set_yticks([])
        else:
            axs[n].set_ylabel('Attack Method', fontsize=6)
            axs[n].set_yticks(range(len(axis_ticklables[args.x_axis])))
            axs[n].set_yticklabels(axis_ticklables[args.x_axis], fontsize=6)

        # set the title of the subplot
        axs[n].set_title(ticklabel_n, fontsize=8, fontweight='bold')

        # set the tick direction and width
        axs[n].xaxis.set_tick_params(which='both', labelbottom=True)
        # set the x label and x ticks
        axs[n].tick_params(direction='in')
        axs[n].tick_params(width=0.5)
        # set the x grid at the backgroud
        axs[n].xaxis.grid(True)
        axs[n].xaxis.grid(linewidth=0.1)
        axs[n].set_axisbelow(True)
        axs[n].set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        axs[n].set_xlim([0, 1.0])
        if n // columns == rows - 1:
            axs[n].set_xticklabels(['0', '20', '40', '60', '80', '100'], fontsize=6)
            axs[n].set_xlabel(f'{args.y_axis}(%) / ASR(%)', fontsize=6)
        else:
            axs[n].set_xticklabels([])


    # set the margin of the plot
    plt.tight_layout()

    # save the plot to pdf
    plt.savefig(args.save_path, dpi=300)
    