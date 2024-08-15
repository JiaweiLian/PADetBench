from calendar import c
import os
from os.path import realpath
import subprocess
import time
from multiprocessing import Process
import yaml
from csv_tools import save_to_csv, read_from_csv, rows_filter, get_current_time, fields_select


def get_config_list(config_dir_path):

    # load the name of candidate model for evaluation
    yml_path = 'model_list.yml'
    if os.path.exists(yml_path):
        with open(yml_path, 'r') as f:
            model_list = yaml.safe_load(f)

    # load the model's config for evaluation
    config_list = list()
    # create a directory to save config and checkpoint files
    if not os.path.exists('checkpoints'):
        os.mkdir('checkpoints')

    # list all the available models
    for model_name in os.listdir(config_dir_path):
        config_path = os.path.join(config_dir_path, model_name)
        yml_path = os.path.join(config_path, 'metafile.yml')
        if os.path.exists(yml_path):
            with open(yml_path, 'r') as f:
                config = yaml.safe_load(f)
                # print all the submodels
                if 'Models' in config:
                    config = config['Models']
                for submodel in config:
                    if submodel['Name'] not in model_list:
                        continue
                    py_path = os.path.join(config_path, submodel['Name'] + '.py')
                    submodel['model_config_path'] = realpath(py_path)
                    config_list.append(submodel)

    return config_list
    
def get_checkpoint_path(model):
    checkpoint_path = os.path.join('checkpoints', model["Name"] + '.pth')
    checkpoint_hash_path = os.path.join('checkpoints', model["Name"] + '.md5')
    checkpoint_url = model["Weights"]
    if os.path.exists(checkpoint_path) and os.path.exists(checkpoint_hash_path):
        # get the hash of the local model
        current_model_hash = subprocess.run(['md5sum', checkpoint_path], stdout=subprocess.PIPE).stdout.decode().split()[0]
        with open(checkpoint_hash_path, 'r') as f:
            model_hash = f.read().strip()
        if current_model_hash == model_hash:
            return checkpoint_path

    print(f"{get_current_time()}: Downloading the checkpoint of the model {model['Name']}...")
    try:
        subprocess.run(['wget', checkpoint_url, '-O', checkpoint_path], stdout=subprocess.PIPE).stdout.decode()
    except:
        print(f"{get_current_time()}: Failed to download the checkpoint of the model {model['Name']}.")
    # get the hash of the downloaded model
    model_hash = subprocess.run(['md5sum', checkpoint_path], stdout=subprocess.PIPE).stdout.decode().split()[0]
    with open(checkpoint_hash_path, 'w') as f:
        f.write(model_hash)
    return checkpoint_path

def get_dataset_list(data_path):
    dataset_list = list()
    for dataset_name in os.listdir(data_path):
        dataset_path = os.path.join(data_path, dataset_name)
        if os.path.isdir(dataset_path):
            dataset_list.append({'Name': dataset_name, 'Path': realpath(dataset_path)})
    return dataset_list

def link_all(from_path, to_path, exclude=[]):
    # remove all the existing symbol links in the data/coco directory
    for file_name in os.listdir(to_path):
        file_path = os.path.join(to_path, file_name)
        if os.path.islink(file_path):
            os.unlink(file_path)

    # create symbol links of all the files in the given dataset in data/coco
    for file_name in os.listdir(from_path):
        if file_name in exclude:
            continue
        file_path = os.path.join(from_path, file_name)
        file_path = os.path.realpath(file_path)
        link_path = os.path.join(to_path, file_name)
        os.symlink(file_path, link_path)

def test_model(benchmark_info, model, dataset, gpu_id):
    model_config_path = os.path.realpath(model['model_config_path'])
    model_checkpoint_path = os.path.realpath(get_checkpoint_path(model))
    
    # link the dataset to the data/coco directory
    link_all(dataset['Path'], os.path.join('data', 'coco'))
    # setting the environment variable for subproces
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
    # run the test script
    try:
        subprocess_instance = subprocess.Popen(['python', os.path.join('tools', 'test.py'), model_config_path, model_checkpoint_path], stdout=subprocess.PIPE)
        stdout, stderr = subprocess_instance.communicate(timeout=1200)
    except subprocess.TimeoutExpired:
        subprocess_instance.terminate()
        raise ValueError("The test results are not complete.")

    # get the test results
    try:
        output = stdout.decode().splitlines()
        fields = [*benchmark_info[0], 'mAP_50_95', 'mAP_50', 'mAR_50_95', 'mAR_50']
        row = [
            *benchmark_info[1],
            rows_filter(output, 'Average Precision', 'area=   all', 'IoU=0.50:0.95')[0].split()[-1],
            rows_filter(output, 'Average Precision', 'area=   all', 'IoU=0.50     ')[0].split()[-1],
            rows_filter(output, 'Average Recall', 'area=   all', 'IoU=0.50     ')[0].split()[-1],
            rows_filter(output, 'Average Recall', 'area=   all', 'IoU=0.50:0.95')[0].split()[-1],
        ]
        return fields, row
    except:
        raise ValueError("The test results are not correct.")

def run_benchmark(running_pwd, benchmark_info, model, dataset, gpu_id, result_path):
    # change the working directory to the running directory
    os.chdir(running_pwd)

    try:
        # check if the model has been tested on the dataset
        headers, row = read_from_csv(result_path)
        _, result_field_list = fields_select((headers, row), benchmark_info[0])
        if list(benchmark_info[1][0]) in result_field_list:
            print(f"{get_current_time()}: The model {model['Name']} has been tested on the dataset {dataset['Name']}.")
            return
        
        # test the model
        print(f"{get_current_time()}: Testing the model {model['Name']} on the dataset {dataset['Name']}...")
        result = test_model(benchmark_info, model, dataset, gpu_id)

        # save the results to a csv file
        save_to_csv(result_path, result)
        print(f"{get_current_time()}: Finished testing the model {model['Name']} on the dataset {dataset['Name']}.")

    except Exception as ValueError:
        print(f"{get_current_time()}: Error: {ValueError} in testing the model {model['Name']}")

def get_args():
    import argparse
    parser = argparse.ArgumentParser(description='Test the models')
    parser.add_argument('--data-path', default='dataset', type=str, help='The path to all the datasets')
    parser.add_argument('--detection-path', default='mmdetection', type=str, help='The path to the detection path', choices=['mmdetection', 'mmyolo'])
    parser.add_argument('--gpus', default=1, type=int, help='The number of GPUs to use')
    parser.add_argument('--result-path', default='results/results.csv', type=str, help='The path to save the results')
    return parser.parse_args()

def main():
    args = get_args()

    result_path = realpath(args.result_path)
    if not os.path.exists(result_path):
        with open(result_path, 'w') as f:
            pass

    config_list = get_config_list(os.path.join(args.detection_path, 'configs'))
    dataset_list = get_dataset_list(args.data_path)

    process_list = list()
    for dataset in dataset_list:
        for model in config_list:

            # get the fields of the results
            actor_type, adv_type, benchmark = dataset['Name'].split('_')
            benchmark_info = [
                ['actor_type', 'adv_type', 'benchmark', 'model_name'],
                [actor_type, adv_type, benchmark, model['Name']],
            ]

            waiting_iteration = 0
            while True:
                # remove the finished processes
                process_list = [process for process in process_list if process['process'].is_alive()]

                from gpu_tools import wait_for_free_gpus
                free_gpu_ids = wait_for_free_gpus()

                # remove the potentially occupied GPUs
                # because the previous testing may not start yet 
                # and will not be detected by the wait_for_free_gpus function
                available_gpu_ids = [gpu_id for gpu_id in free_gpu_ids if not any(process['gpu_id'] == gpu_id for process in process_list)]
                if len(available_gpu_ids) > 0 and len(process_list) < args.gpus: 
                    break
                # print the running processes every minute
                if waiting_iteration % 60 == 0:
                    print(f"{get_current_time()}: Running processes: {*[(process['process'].pid, process['gpu_id'], int(time.time() - process['start_time']), process['model']['Name'], process['dataset']['Name']) for process in process_list],}")
                time.sleep(1)
                waiting_iteration += 1
                
            gpu_id = available_gpu_ids[0]
            running_pwd = f'.running_dir_{gpu_id}'
            os.makedirs(running_pwd, exist_ok=True)
            os.makedirs(os.path.join(running_pwd, 'data', 'coco'), exist_ok=True)
            link_all(args.detection_path, running_pwd, exclude=['data'])
            p = Process(target=run_benchmark, args=(running_pwd, benchmark_info, model, dataset, gpu_id, result_path))
            p.start()
            process_list.append({'process': p, 'gpu_id': gpu_id, 'start_time': time.time(), 'model': model, 'dataset': dataset})
         
if __name__ == '__main__':
    main()   
