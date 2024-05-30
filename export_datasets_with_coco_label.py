from ast import arg

from traitlets import default
import carla
import random
import math
import time
import os
import argparse
import sys
import keyboard
import numpy as np
import cv2
import json
from tick import Weather, Camera, Actor
from data_process import DatasetGenerator


def run(
        dataset_name = 'dataset',  # Define the dataset name
        save_path = 'data',  # Define the output directory
        map='Town10HD_Opt',  # Name of the map
        spawn_point=0,  # Index of the spawn point: 0-154 (Town10HD_Opt)
        vehicle_blueprint_id='vehicle.audi.etron',  # Blueprint ID of the vehicle
        theta_list = [math.pi/3],  # Rotation range of the camera
        phi_list = [0],  # Height of the spectator
        radius_list = [5],  # Enable dolly
        weather_list = [100],  # Enable weather changing
        
):

    # Connect to the client and retrieve the world object
    client = carla.Client('localhost', 2000)
    world = client.load_world(map)
    
    # create a vehicle
    vehicle = Actor(world, vehicle_blueprint_id, spawn_point)

    # Set up the simulator in synchronous mode
    settings = world.get_settings()
    settings.synchronous_mode = True # Enables synchronous mode
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    # create a camera
    camera = Camera(world, vehicle)

    # weather_update_freq = 0.1 / speed_weather_changing
    weather = Weather(world)

    # Create the dataset generator
    datasetGenerator = DatasetGenerator(world, camera, save_path, dataset_name)
    
    iteration_len = max(len(theta_list), len(phi_list), len(radius_list), len(weather_list))
    if iteration_len != min(len(theta_list), len(phi_list), len(radius_list), len(weather_list)):
        print('The length of the lists must be the same')
        return
    for i in range(iteration_len):
        camera.rotate(theta_list[i], phi_list[i])
        camera.dolly(radius_list[i])
        weather.tick(weather_list[i])

        sys.stdout.write('\r' + str(weather) + 12 * ' ')
        sys.stdout.flush()

        camera_transform_before_tick = camera.get_transform()
        while camera_transform_before_tick == camera.get_transform():
            time.sleep(0.0001)
            world.tick()



        # Save the data in the pascal voc format
        # datasetGenerator.save_data(save_images=True, save_pascal_voc=True, save_images_with_2d_bb=True, save_images_with_3d_bb=True)
        datasetGenerator.save_data(save_images=True)

        if keyboard.is_pressed('q'):  
            print('You pressed q, loop will break')
            break  # exit loop
    
    datasetGenerator.annotation_save()

    # Destroy the vehicle
    del vehicle

    settings.synchronous_mode = False # Enables synchronous mode
    world.apply_settings(settings)

if __name__ == '__main__':
    # Name the output directory with the rotation speed and the weather speed
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_path', type=str, default='data', help='Name of the output directory')
    parser.add_argument('--map', type=str, default='Town10HD_Opt', help='Name of the map')
    parser.add_argument('--benchmark', type=str, choices=['entire', 'weather', 'distance', 'rotation-theta', 'rotation-phi', 'spot', 'random'], default='entire', help='Name of the benchmark')

    args = parser.parse_args()
    
    dataset_len = 100
    theta_list = [math.pi/3] * dataset_len
    phi_list = [0] * dataset_len
    radius_list = [5] * dataset_len
    weather_list = [100] * dataset_len

    if args.benchmark == 'rotation-theta':
        dataset_name='rotation-theta'
        theta_list = [i/dataset_len * (math.pi / 2) for i in range(dataset_len)]
    if args.benchmark == 'rotation-phi':
        dataset_name='rotation-phi'
        phi_list = [i/dataset_len * (2 * math.pi) for i in range(dataset_len)]
    if args.benchmark == 'distance':
        dataset_name='distance'
        radius_list = [i/dataset_len * 10 + 4 for i in range(dataset_len)]
    if args.benchmark == 'weather':
        dataset_name='weather'
        weather_list = [i * 1 for i in range(dataset_len)]
    if args.benchmark == 'random':
        len = 10000
        rotate_angles = [random.randint(0, 360) for _ in range(len)]
        dolly_radius = [random.randint(1, 50) for _ in range(len)]
        weather_deltas = range(0,len,10)
    run(dataset_name=dataset_name, save_path=args.save_path, map=args.map, theta_list=theta_list, phi_list=phi_list, radius_list=radius_list, weather_list=weather_list)
