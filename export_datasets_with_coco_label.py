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
        vehicle_blueprint_id='vehicle.audi.etron_white',  # Blueprint ID of the vehicle
        rotate_angles = [0],  # Rotation range of the camera
        dolly_radius = [10],  # Enable dolly
        dolly_heights = [5],  # Height of the spectator
        weather_deltas = range(0,1000,10),  # Enable weather changing
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

    iteration_len = max(len(rotate_angles), len(dolly_radius), len(dolly_heights), len(weather_deltas))
    for i in range(iteration_len):
        camera.rotate(rotate_angles[i%len(rotate_angles)])
        camera.dolly(dolly_radius[i%len(dolly_radius)], dolly_heights[i%len(dolly_heights)])
        weather.tick(weather_deltas[i%len(weather_deltas)]-weather_deltas[(i-1)%len(weather_deltas)])

        sys.stdout.write('\r' + str(weather) + 12 * ' ')
        sys.stdout.flush()

        world.tick()

        # Save the data in the pascal voc format
        datasetGenerator.save_data(save_images=True, save_pascal_voc=True, save_images_with_2d_bb=True, save_images_with_3d_bb=True)

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
    parser.add_argument('--benchmark', type=str, choices=['entire', 'weather', 'distance', 'rotation', 'spot', 'random'], default='entire', help='Name of the benchmark')

    args = parser.parse_args()

    if args.benchmark == 'weather' or args.benchmark == 'entire':
        run(dataset_name='weather', save_path=args.save_path, map=args.map, weather_deltas=range(0,10000,10))
    if args.benchmark == 'distance' or args.benchmark == 'entire':
        run(dataset_name='distance', save_path=args.save_path, map=args.map, dolly_radius=range(1, 10, 1))
    if args.benchmark == 'rotation' or args.benchmark == 'entire':
        run(dataset_name='rotation', save_path=args.save_path, map=args.map, rotate_angles=range(0, 360, 1))
    if args.benchmark == 'random' or args.benchmark == 'entire':
        len = 10000
        rotate_angles = [random.randint(0, 360) for _ in range(len)]
        dolly_radius = [random.randint(1, 50) for _ in range(len)]
        weather_deltas = range(0,len,10)
        run(dataset_name='random', save_path=args.save_path, map=args.map, rotate_angles=rotate_angles, dolly_radius=dolly_radius, dolly_heights=[5], weather_deltas=weather_deltas)
