import carla
import random
import math
import time
import os
import argparse
import sys
import keyboard
import queue
import numpy as np
import cv2
from pascal_voc_writer import Writer
import keyboard
import json
from weather_tick import Weather


def run(
        map='Town10HD_Opt',  # Name of the map
        radius=6,  # Radius of the spectator rotation circle
        height=3,  # Height of the spectator
        spawn_point=0,  # Index of the spawn point: 0-154 (Town10HD_Opt)
        speed_rotation_degree = 1.0,  # Define the speed of the rotation (degree)
        vehicle_blueprint_id='vehicle.audi.etron_white',  # Blueprint ID of the vehicle
        sensor_blueprint_id='sensor.camera.rgb',  # Blueprint ID of the sensor 
        image_width='800',  # Define the width of the image
        image_height='600',  # Define the height of the image
        output_dir = r'data',  # Define the output directory
        save_images = False,  # Define if the images should be saved
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

    angle_radian = 0.0  # Initial angle_radian of the spectator
    angle_degree = 0.0  # Initial angle_degree of the spectator

    # Get the spectator
    spectator = world.get_spectator()

    # Create a blueprint for the camera
    camera_blueprint = world.get_blueprint_library().find(sensor_blueprint_id)
    camera_blueprint.set_attribute('image_size_x', image_width)
    camera_blueprint.set_attribute('image_size_y', image_height)
    # Attach the camera to the spectator
    # The camera's transform relative to the spectator is set same as camera attach to the ego vehicle, otherwise the calculated bounding box will be inaccurate
    camera_initial_transform = carla.Transform(carla.Location(x=0.0, y=0.0, z=2.0))  
    camera = world.spawn_actor(camera_blueprint, camera_initial_transform, attach_to=spectator)

    # Get the world to camera matrix
    world_2_camera = np.array(camera.get_transform().get_inverse_matrix())

    # Get the attributes from the camera
    image_w = camera_blueprint.get_attribute("image_size_x").as_int()
    image_h = camera_blueprint.get_attribute("image_size_y").as_int()
    fov = camera_blueprint.get_attribute("fov").as_float()

    # Calculate the camera projection matrix to project from 3D -> 2D
    K = build_projection_matrix(image_w, image_h, fov)

    # Remember the edge pairs
    edges = [[0,1], [1,3], [3,2], [2,0], [0,4], [4,5], [5,1], [5,7], [7,6], [6,4], [6,2], [7,3]]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # weather_update_freq = 0.1 / speed_weather_changing
    weather = Weather(world.get_weather())

    # Name the output directory with the rotation speed and the weather speed
    folder_name = 'output' + '_rs%02.2f' % speed_rotation_degree + '_ws%02.2f' % speed_weather_changing + "_" + vehicle_blueprint_id.split('.')[-1]
    output_dir = os.path.join(output_dir, folder_name.replace('.', '_'))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    coco_label_json = {
        "info": ['none'], 
        "license": ['none'], 
        "images": [], 
        "categories": [], 
        "annotations": []
        }

    annotation_id = 1

    coco_categories = {'person': 0, 'bicycle': 1, 'car': 2, 'motorcycle': 3, 'airplane': 4, 'bus': 5, 'train': 6, 'truck': 7, 'boat': 8, 'traffic light': 9, 'fire hydrant': 10, 'stop sign': 11, 'parking meter': 12, 'bench': 13, 'bird': 14, 'cat': 15, 'dog': 16, 'horse': 17, 'sheep': 18, 'cow': 19, 'elephant': 20, 'bear': 21, 'zebra': 22, 'giraffe': 23, 'backpack': 24, 'umbrella': 25, 'handbag': 26, 'tie': 27, 'suitcase': 28, 'frisbee': 29, 'skis': 30, 'snowboard': 31, 'sports ball': 32, 'kite': 33, 'baseball bat': 34, 'baseball glove': 35, 'skateboard': 36, 'surfboard': 37, 'tennis racket': 38, 'bottle': 39, 'wine glass': 40, 'cup': 41, 'fork': 42, 'knife': 43, 'spoon': 44, 'bowl': 45, 'banana': 46, 'apple': 47, 'sandwich': 48, 'orange': 49, 'broccoli': 50, 'carrot': 51, 'hot dog': 52, 'pizza': 53, 'donut': 54, 'cake': 55, 'chair': 56, 'couch': 57, 'potted plant': 58, 'bed': 59, 'dining table': 60, 'toilet': 61, 'tv': 62, 'laptop': 63, 'mouse': 64, 'remote': 65, 'keyboard': 66, 'cell phone': 67, 'microwave': 68, 'oven': 69, 'toaster': 70, 'sink': 71, 'refrigerator': 72, 'book': 73, 'clock': 74, 'vase': 75, 'scissors': 76, 'teddy bear': 77, 'hair drier': 78, 'toothbrush': 79}

    for caftegory, category_id in coco_categories.items():
        coco_label_json['categories'].append({'supercategory': 'none', 'id': category_id, 'name': caftegory})

    # time.sleep(3)  # Wait for the car landing before taking the first image

    # Create a queue to store and retrieve the sensor data
    image_queue = queue.Queue()
    camera.listen(image_queue.put)

    while angle_degree < total_rotation_degree:
        # Calculate the transform of the spectator
        transform = rotation_transform_update(vehicle, radius, height, angle_radian)
        transform.location.z -= 2.0
        # Set the transform of the spectator
        spectator.set_transform(transform) 

        # Update the weather
        weather.tick(speed_weather_changing)
        world.set_weather(weather.weather)
        sys.stdout.write('\r' + str(weather) + 12 * ' ')
        sys.stdout.flush()

        world.tick()
        image = image_queue.get()

        # Get the camera matrix 
        world_2_camera = np.array(camera.get_transform().get_inverse_matrix())

        img = np.reshape(np.copy(image.raw_data), (image.height, image.width, 4))

        weather_string = str(weather).replace(' ', '_').replace(':', '').replace(',', '').replace('(', '_').replace(')', '').replace('=', '').replace('%', '').replace('.', '_')
        # image_id = '%06d' % angle_degree + '_R%02d' % radius + '_H%02d_' % height + weather_string + '_' + map  # Detailed information of the image
        image_id = '%06d' % angle_degree
        image_name = image_id + '.png'

        image_json = {'file_name': image_name, 'height': image.height, 'width': image.width, 'id': int(image_id)}
        coco_label_json['images'].append(image_json)

        output_path = os.path.join(output_dir, image_name)
        # Save the image
        if save_images:
            image.save_to_disk(output_path)

        # Initialize the exporter of pascal voc format
        writer = Writer(output_path, image_w, image_h)

        for npc in world.get_actors().filter('*vehicle*'):
            bb = npc.bounding_box
            dist = npc.get_transform().location.distance(spectator.get_transform().location)
            if dist < 50:
                forward_vec = spectator.get_transform().get_forward_vector()
                ray = npc.get_transform().location - spectator.get_transform().location
                if forward_vec.dot(ray) > 1:
                    p1 = get_image_point(bb.location, K, world_2_camera)
                    verts = [v for v in bb.get_world_vertices(npc.get_transform())]
                    if save_images_with_3d_bb:
                        for edge in edges:
                            p1 = get_image_point(verts[edge[0]], K, world_2_camera)
                            p2 = get_image_point(verts[edge[1]],  K, world_2_camera)
                            cv2.line(img, (int(p1[0]),int(p1[1])), (int(p2[0]),int(p2[1])), (255,0,0, 255), 1)        

                    x_max = -10000
                    x_min = 10000
                    y_max = -10000
                    y_min = 10000
                    for vert in verts:
                        p = get_image_point(vert, K, world_2_camera)
                        # Find the rightmost vertex
                        if p[0] > x_max:
                            x_max = p[0]
                        # Find the leftmost vertex
                        if p[0] < x_min:
                            x_min = p[0]
                        # Find the highest vertex
                        if p[1] > y_max:
                            y_max = p[1]
                        # Find the lowest  vertex
                        if p[1] < y_min:
                            y_min = p[1]
                    if save_images_with_2d_bb:
                        cv2.line(img, (int(x_min),int(y_min)), (int(x_max),int(y_min)), (0,0,255, 255), 1)
                        cv2.line(img, (int(x_min),int(y_max)), (int(x_max),int(y_max)), (0,0,255, 255), 1)
                        cv2.line(img, (int(x_min),int(y_min)), (int(x_min),int(y_max)), (0,0,255, 255), 1)
                        cv2.line(img, (int(x_max),int(y_min)), (int(x_max),int(y_max)), (0,0,255, 255), 1)

                    # Add the object to the frame (ensure it is inside the image)
                    if x_min > 0 and x_max < image_w and y_min > 0 and y_max < image_h: 
                        writer.addObject('car', x_min, y_min, x_max, y_max)

                        npc_width = abs(x_max - x_min)
                        npc_height = abs(y_max - y_min)
                        annotation = {'area': npc_width * npc_height, 
                                    'iscrowd': 0, 
                                    'image_id': int(image_id), 
                                    'bbox': [x_min, y_min, npc_width, npc_height], 
                                    'category_id': coco_categories['car'], 
                                    'id': annotation_id, 
                                    'ignore': 0, 
                                    'segmentation': []
                                    }
                        coco_label_json['annotations'].append(annotation)
                        annotation_id += 1

        if save_pascal_voc:
            # Save the bounding boxes in the scene
            writer.save(output_path.replace('.png', '.xml'))

        # Calculate the angle_radian based on the speed
        angle_radian += (math.pi * 2.0 / 360.0) * speed_rotation_degree
        angle_degree += speed_rotation_degree

        if save_images_with_bb:
            cv2.imwrite(output_path.replace('.png', '_bb.png'), img)

        if keyboard.is_pressed('q'):  
            print('You pressed q, loop will break')
            break  # exit loop
    vehicle.destroy()
    with open(os.path.join(output_dir, 'coco_label.json'), 'w') as f:
        json.dump(coco_label_json, f)

    settings.synchronous_mode = False # Enables synchronous mode
    world.apply_settings(settings)

def world_tick(n, world):
    for i in range(n):
        world.tick()

def build_projection_matrix(w, h, fov):
    focal = w / (2.0 * np.tan(fov * np.pi / 360.0))
    K = np.identity(3)
    K[0, 0] = K[1, 1] = focal
    K[0, 2] = w / 2.0
    K[1, 2] = h / 2.0
    return K

def get_image_point(loc, K, w2c):
        # Calculate 2D projection of 3D coordinate

        # Format the input coordinate (loc is a carla.Position object)
        point = np.array([loc.x, loc.y, loc.z, 1])
        # transform to camera coordinates
        point_camera = np.dot(w2c, point)

        # New we must change from UE4's coordinate system to an "standard"
        # (x, y ,z) -> (y, -z, x)
        # and we remove the fourth componebonent also
        point_camera = [point_camera[1], -point_camera[2], point_camera[0]]

        # now project 3D->2D using the camera matrix
        point_img = np.dot(K, point_camera)
        # normalize
        point_img[0] /= point_img[2]
        point_img[1] /= point_img[2]

        return point_img[0:2]

# Define a function that calculates the transform of the spectator
def rotation_transform_update(vehicle, radius, height, angle_radian):
    # Get the location of the vehicle
    vehicle_location = vehicle.get_location()

    # Calculate the new location of the spectator
    location = carla.Location()
    location.x = vehicle_location.x + radius * math.cos(angle_radian)  # X-coordinate
    location.y = vehicle_location.y + radius * math.sin(angle_radian)  # Y-coordinate
    location.z = vehicle_location.z + height                    # Z-coordinate

    # Calculate the rotation that makes the spectator look at the vehicle
    rotation = carla.Rotation()
    rotation.yaw = math.degrees(angle_radian) + 180 # Yaw angle_radian
    rotation.pitch = -math.degrees(math.atan(height / radius))  # Pitch angle_radian

    # Create a new transform with the new location and the new rotation
    transform = carla.Transform(location, rotation)
    return transform

# Define a function to save images
def save_image(image, output_path, angle_degree):
    # Save the image to disk
    image.save_to_disk(output_path)

if __name__ == '__main__':
    run()
