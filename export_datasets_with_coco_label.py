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
        map='Town10HD_Opt',  # Name of the map
        radius=10,  # Radius of the spectator rotation circle
        height=5,  # Height of the spectator
        spawn_point=0,  # Index of the spawn point: 0-154 (Town10HD_Opt)
        speed_rotation_degree = 1.0,  # Define the speed of the rotation (degree)
        vehicle_blueprint_id='vehicle.audi.etron_white',  # Blueprint ID of the vehicle
        save_path = r'data',  # Define the output directory
        speed_weather_changing = 10.0,  # Define the speed of the weather changing
        total_rotation_degree = math.inf  # Define the total rotation degree
):
    # Connect to the client and retrieve the world object
    client = carla.Client('localhost', 2000)
    world = client.load_world(map)

    # Set up the simulator in synchronous mode
    settings = world.get_settings()
    settings.synchronous_mode = True # Enables synchronous mode
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    # create a vehicle
    vehicle = Actor(world, vehicle_blueprint_id, spawn_point)

    # create a camera
    camera = Camera(world, vehicle, radius, height)

    # weather_update_freq = 0.1 / speed_weather_changing
    weather = Weather(world)

    # Name the output directory with the rotation speed and the weather speed
    dataset_name = 'output' + '_rs%02.2f' % speed_rotation_degree + '_ws%02.2f' % speed_weather_changing + "_" + vehicle_blueprint_id.split('.')[-1]

    # Create the dataset generator
    datasetGenerator = DatasetGenerator(world, camera, save_path, dataset_name)

    while camera.angle_degree < total_rotation_degree:
        # Update the spectator
        camera.tick(speed_rotation_degree)

        # Update the weather
        weather.tick(speed_weather_changing)

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
    run()
