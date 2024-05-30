from ast import arg
from calendar import c

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
        world,  # Name of the map
        settings,  # Settings for the dataset generation
        dataset_name = 'dataset',  # Define the dataset name
        save_path = 'data',  # Define the output directory
):
    
    # create a vehicle
    vehicle = Actor(world)

    # weather_update_freq = 0.1 / speed_weather_changing
    weather = Weather(world)

    # create a camera
    camera = Camera(world, vehicle)

    # Create the dataset generator
    datasetGenerator = DatasetGenerator(world, camera, save_path, dataset_name)
    
    iteration_len = len(settings['theta_list'])
    for i in range(iteration_len):
        world_settings = world.get_settings()
        world_settings.synchronous_mode = False # Enables synchronous mode
        world.apply_settings(settings)

        
        vehicle.create_actor(settings['blueprint_list'][i], settings['spawnpoint_list'][i])
        world_settings = world.get_settings()
        world_settings.synchronous_mode = True # Enables synchronous mode
        world.apply_settings(settings)


        camera.follow(vehicle)
        camera.rotate(settings['theta_list'][i], settings['phi_list'][i])
        camera.dolly(settings['radius_list'][i])
        weather.tick(settings['weather_list'][i])

        sys.stdout.write('\r' + str(weather) + 12 * ' ')
        sys.stdout.flush()

        # Save the data in the pascal voc format
        # datasetGenerator.save_data(save_images=True, save_pascal_voc=True, save_images_with_2d_bb=True, save_images_with_3d_bb=True)
        datasetGenerator.save_data(save_images=True)

        if keyboard.is_pressed('q'):  
            print('You pressed q, loop will break')
            break  # exit loop
    
    datasetGenerator.annotation_save()

    # Destroy the vehicle
    del vehicle


def world_init(map):
    # Connect to the client and retrieve the world object
    client = carla.Client('localhost', 2000)
    world = client.load_world(map)

    # Set up the simulator in synchronous mode
    settings = world.get_settings()
    settings.synchronous_mode = True # Enables synchronous mode
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    return world

def world_close(world):
    settings = world.get_settings()
    settings.synchronous_mode = False # Enables synchronous mode
    world.apply_settings(settings)

def settings_complete(settings, dataset_len=100):
    if 'spawnpoint_list' not in settings:
        settings['spawnpoint_list'] = [world.get_map().get_spawn_points()[0]] * dataset_len
    if 'blueprint_list' not in settings:
        settings['blueprint_list'] = [world.get_blueprint_library().filter('vehicle.*')[0]] * dataset_len
    if 'theta_list' not in settings:
        settings['theta_list'] = [math.pi/3] * dataset_len
    if 'phi_list' not in settings:
        settings['phi_list'] = [0] * dataset_len
    if 'radius_list' not in settings:
        settings['radius_list'] = [5] * dataset_len
    if 'weather_list' not in settings:
        settings['weather_list'] = [100] * dataset_len

    return settings

if __name__ == '__main__':
    # Name the output directory with the rotation speed and the weather speed
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_path', type=str, default='data', help='Name of the output directory')
    parser.add_argument('--map', type=str, default='Town10HD_Opt', help='Name of the map')
    parser.add_argument('--benchmark', type=str, choices=['vehicle', 'weather', 'distance', 'rotation-theta', 'rotation-phi', 'spot', 'random'], default='entire', help='Name of the benchmark')
    args = parser.parse_args()

    world = world_init(args.map)    

    # default settings
    default_dataset_len = 100
    settings = dict()

    # benchmark settings
    if args.benchmark == 'vehicle':
        dataset_name='vehicle'
        settings['blueprint_list'] = world.get_blueprint_library().filter('vehicle.*')
        dataset_len = len(settings['blueprint_list'])
    if args.benchmark == 'spot':
        dataset_name='spot'
        settings['spawnpoint_list'] = world.get_map().get_spawn_points()
        dataset_len = len(settings['spawnpoint_list'])
    if args.benchmark == 'rotation-theta':
        dataset_name='rotation-theta'
        dataset_len = default_dataset_len
        settings['theta_list'] = [i/dataset_len * (math.pi / 2) for i in range(dataset_len)]
    if args.benchmark == 'rotation-phi':
        dataset_name='rotation-phi'
        dataset_len = default_dataset_len
        settings['phi_list'] = [i/dataset_len * (2 * math.pi) for i in range(dataset_len)]
    if args.benchmark == 'distance':
        dataset_name='distance'
        dataset_len = default_dataset_len
        settings['radius_list'] = [i/dataset_len * 10 + 4 for i in range(dataset_len)]
    if args.benchmark == 'weather':
        dataset_name='weather'
        settings['weather_list'] = [i * 1 for i in range(dataset_len)]
    
    settings = settings_complete(settings, dataset_len)

    run(world=world, settings=settings, dataset_name=dataset_name, save_path=args.save_path)

    world_close(world)
    