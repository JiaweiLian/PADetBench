from turtle import color
from matplotlib import legend, pyplot as plt
import numpy as np
import pandas as pd
import random
from scipy.interpolate import make_interp_spline
from scipy.interpolate import pchip

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='plot')
    parser.add_argument('--benchmark', type=str, choices=['weather', 'distance', 'rotation-theta', 'rotation-phi', 'sphere', 'spot', 'entire'], default='entire', help='Name of the benchmark')
    parser.add_argument('--data-path', default='results/vehicle.csv', type=str, help='The path to the data')
    parser.add_argument('--save-path', default='results/vehicle.pdf', type=str, help='The path to save the plot')
    parser.add_argument('--n-axis', default='adv_type', type=str, help='The field name of n subplots')
    parser.add_argument('--x-axis', default='model_name', type=str, help='The field name of x axis')
    parser.add_argument('--y-axis', default='mAR 50', type=str, help='The field name of y axis')

    args = parser.parse_args()
    
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
    clean_pos = data['adv_type'] == 'Clean'
    # filter out the 'Clean' data
    data_clean = data[clean_pos]
    data = data[~clean_pos]
    for n_field in data['model_name'].unique():
        pos_data = data['model_name'] == n_field
        pos_data_clean = data_clean['model_name'] == n_field
        data.loc[pos_data, 'mAR 50'] = 1 - data[pos_data]['mAR 50']/data_clean[pos_data_clean]['mAR 50'].values

    # sort the data based on the mAR 50
    data_x_sum = data.groupby(args.x_axis)['mAR 50'].sum()
    sorted_keys = data_x_sum.sort_values(ascending=False).keys()
    # according to the sorted keys, sort the data
    data_new = pd.DataFrame()
    for key in sorted_keys:
        data_new = pd.concat([data_new, data[data[args.x_axis] == key]])
    data = data_new
    

    # plot the data
    font = 'Times New Roman'
    marker = ['X', 'o', 's', 'v', '^', '<', '>', 'p', 'P', '*', 'h', 'H', '+', 'x', '|', '_']
    cm = plt.get_cmap(random.choice(['tab20', 'tab20b', 'tab20c']))
    xy_curve = []

    # set the figure size
    plt.figure(figsize=(10, 3.8))

    # iterate over the n fields
    legend = pd.read_csv(f'results/mapping_{args.n_axis}.csv')['to']
    legend = legend[legend!='Clean']
    legend = legend[legend.isin(data[args.n_axis])]
    legend = legend.sort_values()
    for i, n_field in enumerate(legend):
        data_n = data[data[args.n_axis] == n_field]
        
        # get the x and y axis data
        data_nx = data_n[args.x_axis]
        data_ny = data_n['mAR 50']

        # create integers from strings for interpolation
        idx = range(len(data_nx))
        spl = pchip(idx, data_ny, 1)
        x_curve = np.linspace(min(idx), max(idx), 300)
        y_curve = spl(x_curve)
        xy_curve.append((x_curve, y_curve))

        plt.scatter(data_nx, data_ny, s=60, marker=marker[i], edgecolors=cm(i), color='white', linewidth=1.2, label=n_field)
    
    for i, (x_curve, y_curve) in enumerate(xy_curve):
        plt.plot(x_curve, y_curve, '-', alpha=0.3, color=cm(i))

    # set the legend
    plt.legend(legend, loc='upper right', fontsize=8, frameon=True, edgecolor='black', fancybox=False, borderpad=0.5)
    for text in plt.gca().get_legend().get_texts():
        text.set_fontname(font)
    
    # set the x and y axis labels
    plt.xlabel('Model Name', fontname=font, fontsize=10)
    plt.ylabel('ASR', fontname=font, fontsize=10)
    # set the x and y ticks
    plt.xticks(rotation=45, ha='right', fontsize=8, fontname=font)
    plt.yticks(fontsize=8, fontname=font)
    plt.tick_params(direction='in')
    plt.grid(True, linewidth=0.1)

    
     
    # set the margin of the plot
    plt.tight_layout()

    # set the frame width of the plot
    for spine in plt.gca().spines.values():
        spine.set_linewidth(1)

    # setting the interval between the plots
    plt.subplots_adjust(wspace=0.2, hspace=0.4)

    # save the plot to pdf
    plt.savefig(args.save_path, dpi=300)
    