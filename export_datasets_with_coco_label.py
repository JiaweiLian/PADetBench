from re import A
import carla
import math
import argparse
import sys
import keyboard
import numpy as np
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
        vehicle.create_actor(settings['blueprint_list'][i], settings['spawnpoint_list'][i])
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

def repeat_setting(dataset, iterator):
    try:
        key = next(iterator)
        repeat_len = repeat_setting(dataset, iterator)
        dataset[key] = np.repeat(dataset[key], repeat_len).tolist()
        return len(dataset[key])
    except StopIteration:
        return 1

def settings_complete(blueprint_list, settings, grid=True):

    # default settings
    if 'spawnpoint_list' not in settings:
        settings['spawnpoint_list'] = [world.get_map().get_spawn_points()[0]]
    if 'blueprint_list' not in settings:
        settings['blueprint_list'] = [blueprint for blueprint in blueprint_list if blueprint.id.find('audi.etron')!=-1]
    if 'weather_list' not in settings:
        # weather_delta = 1000 represents sunny weather
        settings['weather_list'] = [1000]
    if 'theta_list' not in settings:
        settings['theta_list'] = [math.pi/3]
    if 'phi_list' not in settings:
        settings['phi_list'] = [0]
    if 'radius_list' not in settings:
        settings['radius_list'] = [7]

    if grid:
        # repeat the settings to match the dataset length
        dataset_len = repeat_setting(settings, iter(settings))
        
        # tile the settings to match the dataset length
        for key in settings:
            settings[key] = settings[key] * (dataset_len // len(settings[key]))

    return settings

def get_blueprint_list(world, actor_type='vehicle', adv_type='clean'):
    example_types = dict()
    example_types['vehicle'] = ['audi.etron', 'tesla.model3', 'nissan.patrol_2021', 'mercedes.coupe_2020', 'bmw.grandtourer', 'chevrolet.impala', 'jeep.wrangler_rubicon', 'mini.cooper_s_2021', 'mercedes.sprinter', 'lincoln.mkz_2020']
    world_blueprint_list = world.get_blueprint_library().filter(actor_type+'.*')
    
    # filter the example types in the blueprint list
    blueprint_list = []
    for example_type in example_types[actor_type]:
        blueprint_list += [blueprint for blueprint in world_blueprint_list if blueprint.id.find(example_type)!=-1]

    # filter the adversarial types in the blueprint list
    if adv_type == 'clean':
        blueprint_list = [blueprint for blueprint in blueprint_list if blueprint.id.find('adv')==-1]
        blueprint_list = [blueprint for blueprint in blueprint_list if blueprint.id.find('random')==-1]
    elif adv_type == 'random':
        blueprint_list = [blueprint for blueprint in blueprint_list if blueprint.id.find('random')!=-1]
    elif adv_type.find('adv') != -1:
        blueprint_list = [blueprint for blueprint in blueprint_list if blueprint.id.find(adv_type)!=-1]
    return blueprint_list
    
def rescale(x, x_min, x_max):
    # rescale x from [0,1] to [x_min, x_max]
    return x * (x_max - x_min) + x_min

if __name__ == '__main__':
    # Name the output directory with the rotation speed and the weather speed
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_path', type=str, default='data', help='Name of the output directory')
    parser.add_argument('--map', type=str, default='Town10HD_Opt', help='Name of the map')
    parser.add_argument('--actor-type', type=str, default='vehicle', help='Name of the dataset')
    parser.add_argument('--adv-type', type=str, default='clean', choices=['clean', 'random', 'active', 'fca', 'dta'], help='Name of the dataset')
    parser.add_argument('--benchmark', type=str, choices=['vehicle', 'weather', 'distance', 'rotation-theta', 'rotation-phi', 'sphere', 'spot', 'entire'], default='entire', help='Name of the benchmark')
    args = parser.parse_args()

    world = world_init(args.map)    

    # default settings
    dataset_name = args.actor_type + '_' + args.adv_type + '_' + args.benchmark
    blueprint_list = get_blueprint_list(world, actor_type=args.actor_type, adv_type=args.adv_type)
    default_dataset_len = 100
    distance_range = (5,15)
    settings = dict()

    # benchmark settings
    if args.benchmark == 'vehicle':
        theta_len = 3
        phi_len = 8
        settings['blueprint_list'] = [blueprint for blueprint in blueprint_list]
        settings['theta_list'] = [i/theta_len * (math.pi / 2) for i in range(1, theta_len)] # without theta = 0, i.e., no overhead view
        settings['phi_list'] = [i/phi_len * (2 * math.pi) for i in range(phi_len)]

    if args.benchmark == 'spot':
        theta_len = 3
        phi_len = 8
        settings['spawnpoint_list'] = world.get_map().get_spawn_points()
        settings['theta_list'] = [i/theta_len * (math.pi / 2) for i in range(1, theta_len)] # without theta = 0, i.e., no overhead view
        settings['phi_list'] = [i/phi_len * (2 * math.pi) for i in range(phi_len)]

    if args.benchmark == 'weather':
        settings['weather_list'] = [i/default_dataset_len * 1000 for i in range(1, default_dataset_len)]

    if args.benchmark == 'rotation-theta':
        settings['theta_list'] = [i/default_dataset_len * (math.pi / 2) for i in range(default_dataset_len)]

    if args.benchmark == 'rotation-phi':
        settings['phi_list'] = [i/default_dataset_len * (2 * math.pi) for i in range(default_dataset_len)]

    if args.benchmark == 'sphere':
        decompose_dataset_len = int(default_dataset_len ** (1/2))
        settings['theta_list'] = [i/decompose_dataset_len * (math.pi / 2) for i in range(1, decompose_dataset_len)] # without theta = 0, i.e., no overhead view
        settings['phi_list'] = [i/decompose_dataset_len * (2 * math.pi) for i in range(decompose_dataset_len)]

    if args.benchmark == 'distance':
        settings['radius_list'] = [rescale(i/default_dataset_len, *distance_range) for i in range(default_dataset_len)]

    if args.benchmark == 'entire':
        theta_len = 3
        phi_len = 8
        weather_len = 10
        distance_len = 5
        settings['blueprint_list'] = blueprint_list[:3]
        settings['spawnpoint_list'] = world.get_map().get_spawn_points()[:3]
        settings['weather_list'] = [40,60,80,100,150,180,200,220,250,280]
        settings['theta_list'] = [i/theta_len * (math.pi / 2) for i in range(1, theta_len)] # without theta = 0, i.e., no overhead view
        settings['phi_list'] = [i/phi_len * (2 * math.pi) for i in range(phi_len)]
        settings['radius_list'] = [rescale(i/distance_len, *distance_range) for i in range(distance_len)]

    settings = settings_complete(blueprint_list, settings)

    run(world=world, settings=settings, dataset_name=dataset_name, save_path=args.save_path)

    world_close(world)
