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
from tick import Weather, Spectator
from data_process import DatasetGenerator


def run(
        map='Town10HD_Opt',  # Name of the map
        radius=6,  # Radius of the spectator rotation circle
        height=3,  # Height of the spectator
        spawn_point=0,  # Index of the spawn point: 0-154 (Town10HD_Opt)
        speed_rotation_degree = 1.0,  # Define the speed of the rotation (degree)
        vehicle_blueprint_id='vehicle.audi.etron_white',  # Blueprint ID of the vehicle
        output_dir = r'data',  # Define the output directory
        save_images_with_bb = False,  # Define if the images with bounding box should be saved
        save_images_with_2d_bb = True,  # Define if the images with 2D bounding box should be saved
        save_images_with_3d_bb = True,  # Define if the images with 3D bounding box should be saved
        save_pascal_voc = False,  # Define if the pascal voc format should be saved
        speed_weather_changing = 10.0,  # Define the speed of the weather changing
        total_rotation_degree = math.inf  # Define the total rotation degree
):
    # Connect to the client and retrieve the world object
    client = carla.Client('localhost', 2000)
    world = client.load_world(map)

    # Get the blueprint library and filter for the vehicle blueprints
    vehicle_blueprint = world.get_blueprint_library().find(vehicle_blueprint_id)

    # Choose a spawn location
    # In this example, we're spawningradius of the circle the vehicle at a random location
    spawn_points = world.get_map().get_spawn_points()  # len(transforms) = 155 for Town10HD_Opt
    vehicle_transform = spawn_points[spawn_point]

    # Spawn the vehicle
    vehicle = world.spawn_actor(vehicle_blueprint, vehicle_transform)
    time.sleep(1)  # Wait for the vehicle to be ready

    # # Wait for the vehicle to be ready
    # world_tick(20, world)

    # Set up the simulator in synchronous mode
    settings = world.get_settings()
    settings.synchronous_mode = True # Enables synchronous mode
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    # Get the spectator
    spectator = Spectator(world.get_spectator(), vehicle, radius, height)

    # Attach the camera to the spectator
    # The camera's transform relative to the spectator is set same as camera attach to the ego vehicle, otherwise the calculated bounding box will be inaccurate

    # weather_update_freq = 0.1 / speed_weather_changing
    weather = Weather(world)

    # Name the output directory with the rotation speed and the weather speed
    folder_name = 'output' + '_rs%02.2f' % speed_rotation_degree + '_ws%02.2f' % speed_weather_changing + "_" + vehicle_blueprint_id.split('.')[-1]

    # Create the dataset generator
    datasetGenerator = DatasetGenerator(world, spectator, output_dir, folder_name)

    # time.sleep(3)  # Wait for the car landing before taking the first image

    while spectator.angle_degree < total_rotation_degree:
        # Update the spectator
        spectator.tick(speed_rotation_degree)

        # Update the weather
        weather.tick(speed_weather_changing)
        sys.stdout.write('\r' + str(weather) + 12 * ' ')
        sys.stdout.flush()

        world.tick()

        # Save the data in the pascal voc format
        datasetGenerator.save_data(save_images=True)

        if keyboard.is_pressed('q'):  
            print('You pressed q, loop will break')
            break  # exit loop
    
    
    datasetGenerator.annotation_save()

    # Destroy the vehicle
    vehicle.destroy()

    settings.synchronous_mode = False # Enables synchronous mode
    world.apply_settings(settings)

def world_tick(n, world):
    for i in range(n):
        world.tick()

# Define a function to save images
def save_image(image, output_path, angle_degree):
    # Save the image to disk
    image.save_to_disk(output_path)

if __name__ == '__main__':
    run()
