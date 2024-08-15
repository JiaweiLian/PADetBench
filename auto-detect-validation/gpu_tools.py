import subprocess
import time
def get_free_gpus(memory_threshold=128):
    """
    Get the list of free GPUs
    """
    # get the list of all GPUs
    gpu_list = subprocess.run(['nvidia-smi', '-L'], stdout=subprocess.PIPE).stdout.decode().split('\n')
    free_gpus = list()
    for gpu in gpu_list:
        if not gpu:
            continue
        gpu_id = int(gpu.split()[1][:-1])
        # get the GPU memory usage
        gpu_memory = subprocess.run(['nvidia-smi', '-i', str(gpu_id), '--query-gpu=memory.used', '--format=csv'], stdout=subprocess.PIPE).stdout.decode().split('\n')
        gpu_memory = int(gpu_memory[1].split()[0])
        if gpu_memory < memory_threshold:
            free_gpus.append(gpu_id)
    return free_gpus

def wait_for_free_gpus(memory_threshold=128, wait_time=10):
    """
    Wait for the free GPUs
    """
    while True:
        free_gpus = get_free_gpus(memory_threshold)
        if len(free_gpus) >= 1:
            break
        time.sleep(wait_time)
    return free_gpus

if __name__ == '__main__':
    print(get_free_gpus())