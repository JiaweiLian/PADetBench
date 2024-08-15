import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import random
from sklearn.manifold import TSNE
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

    tsne = TSNE(n_components=2, verbose=1, perplexity=40, n_iter=300)
    # tsne_results = tsne.fit_transform()

    # set the margin of the plot
    plt.tight_layout()

    # save the plot to pdf
    plt.savefig(args.save_path, dpi=300)
    