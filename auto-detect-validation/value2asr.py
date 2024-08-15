from matplotlib import axis
import pandas as pd

def value2asr(data, y_axis:str):
    data_new = pd.DataFrame()
    data_clean = data[data['adv_type'] == 'Clean']
    for row in data.iloc:
        filter_benchmark = data_clean['benchmark'] == row['benchmark']
        filter_model = data_clean['model_name'] == row['model_name']
        data_new = pd.concat([data_new, pd.DataFrame(
            row.to_dict()
            | {'ASR': 1 - row[y_axis]/data_clean[filter_benchmark & filter_model][y_axis].values}
        )])
    return data_new