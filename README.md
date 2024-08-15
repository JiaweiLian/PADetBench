# PADetBench: Benchmark for Physical Attacks Against Object Detection

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/JiaweiLian/Benchmarking_Physical_Attack)

## Overview

PADetBench is a comprehensive benchmark designed to evaluate the robustness of object detection models against physical attacks. It addresses the challenges associated with conducting real-world physical experiments, which are often time-consuming, labor-intensive, and difficult to standardize. By leveraging realistic simulation, PADetBench ensures a fair and rigorous evaluation of physical attacks under controlled physical dynamics and cross-domain transformations.

![](./images/overview.pdf)

## Features

- **20 Physical Attack Methods**: A wide range of physical attack strategies tailored specifically for object detection tasks.
- **48 Object Detectors**: Includes state-of-the-art detectors, enabling a comprehensive comparison across different architectures.
- **Comprehensive Physical Dynamics**: Simulates diverse environmental conditions such as weather, viewing angles, and distances.
- **Evaluation Metrics**: Provides a set of metrics to assess the effectiveness of attacks and the robustness of detection models.
- **End-to-End Pipelines**: Offers complete workflows for dataset generation, detection, evaluation, and analysis.

## Key Contributions

- **Fair and Rigorous Evaluation**: Ensures that all evaluations are conducted under the same physical dynamics, eliminating inconsistencies found in real-world experiments.
- **Cross-Domain Transformation Control**: Bridges the gap between physical and digital domains, ensuring that adversarial perturbations survive the transformation process.
- **Detailed Analysis**: Provides deep insights into the performance of physical attacks and the robustness of object detection models through extensive experiments.

## Dataset

The dataset is generated using the CARLA simulator, which provides realistic scenes and physical dynamics. The benchmark includes:

- **Scenes**: Various environments with different map configurations and spawn points.
- **Objects**: A diverse range of vehicles (e.g., Audi E-Tron, Tesla Model 3, Nissan Patrol 2021) and pedestrians with adjustable colors and attributes.
- **Camera Parameters**: Half-ball sample space for camera positioning (radius, polar angle, azimuth angle).
- **Physical Dynamics**: Continuous variations including sun angles, cloudiness, precipitation, puddles, wind, fog, and wetness.

## Installation
This document describes the installation of the required software to run the Carla simulator. The installation can be finished in two steps **within a few minutes**. 
### Installation of Docker
For simiplicity, we will use Docker to install Carla. First, we need to install Docker with NVIDIA support:
- Add the GPG key for the official NVIDIA repository to the system:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
    && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```
- Install the NVIDIA container toolkit:
```bash
sudo apt-get update && sudo apt-get install -y nvidia-docker2
```
- Restart the Docker daemon to complete the installation:
```bash
sudo systemctl restart docker
```
- Verify the installation:
```bash
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Installation of Carla
- Allow the X server to accept connections from the Docker container:
```bash
xhost +local:root
```
- Pull the Carla Docker image:
```bash
docker pull carlasim/carla:0.9.13
```
- Run the Carla Docker container:
```bash
docker run --name carlaserver \
    --runtime=nvidia \
    --gpus all \
    -p 2000-2002:2000-2002
    -e SDL_VIDEODRIVER=x11 \
    -e DISPLAY=$DISPLAY \
    -e XAUTHORITY=$XAUTHORITY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -it carlasim/carla \
    ./CarlaUE4.sh
```

## Usage

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/PADetBench.git
   ```
2. Generate datasets:
    ```bash
    python generate_datasets.py
