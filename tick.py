import re
import numpy as np
import math
import queue
import time

from psutil import swap_memory
import carla

def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(value, maximum))

class Sun(object):
    def __init__(self, weather):
        self.weather = weather
        self.init_sun_azimuth_angle = weather.sun_azimuth_angle
        self.reset()
    
    def reset(self):
        self._t = 0.0
        self.azimuth = self.init_sun_azimuth_angle

    def tick(self, delta):
        self._t += 0.008 * delta
        self._t %= 2.0 * math.pi
        self.azimuth += 0.25 * delta
        self.azimuth %= 360.0
        altitude = (70 * math.sin(self._t)) - 20

        self.weather.sun_azimuth_angle = self.azimuth
        self.weather.sun_altitude_angle = altitude

    def __str__(self):
        return 'Sun(alt: %.2f, azm: %.2f)' % (self.weather.sun_altitude_angle, self.weather.sun_azimuth_angle)
    
class Storm:
    def __init__(self, weather):
        self.weather = weather
        self.init_precipitation = weather.precipitation if weather.precipitation > 0.0 else -50.0

    def reset(self):
        self._t = self.init_precipitation
        self._increasing = True

    def tick(self, delta):
        delta = (1.3 if self._increasing else -1.3) * delta
        self._t = clamp(delta + self._t, -250.0, 100.0)
        cloudiness = clamp(self._t + 40.0, 0.0, 90.0)
        precipitation = clamp(self._t, 0.0, 80.0)
        delay = -10.0 if self._increasing else 90.0
        puddles = clamp(self._t + delay, 0.0, 85.0)
        wetness = clamp(self._t * 5, 0.0, 100.0)
        wind_intensity = 5.0 if cloudiness <= 20 else 90 if cloudiness >= 70 else 40
        fog_density = clamp(self._t - 10, 0.0, 30.0)
        if self._t == -250.0:
            self._increasing = True
        if self._t == 100.0:
            self._increasing = False

        self.weather.cloudiness = cloudiness
        self.weather.precipitation = precipitation
        self.weather.precipitation_deposits = puddles
        self.weather.wind_intensity = wind_intensity
        self.weather.fog_density = fog_density
        self.weather.wetness = wetness
        
    def __str__(self):
        return 'Storm(clouds=%d%%, precipitation=%d%%, wind=%d%%)' % (self.weather.cloudiness, self.weather.precipitation, self.weather.wind_intensity)
    
class Weather:
    def __init__(self, world):
        self.world = world
        self.weather = world.get_weather()
        self.sun = Sun(self.weather)
        self.storm = Storm(self.weather)
        self.prev_t = 0
        self.tick(0)

    def tick(self, curr_t):
        delta = curr_t - self.prev_t
        if delta < 0:
            self.sun.reset()
            self.storm.reset()
            delta = curr_t
            
        while delta > 0:
            self.sun.tick(min(delta, 10))
            self.storm.tick(min(delta, 10))
            delta -= 10
        self.world.set_weather(self.weather)
        # Wait until the weather is updated
        for _ in range(5):
            self.world.tick()

        self.prev_t = curr_t

    def __str__(self):
        return '%s %s' % (self.sun, self.storm)

def build_projection_matrix(w, h, fov):
    focal = w / (2.0 * np.tan(fov * np.pi / 360.0))
    K = np.identity(3)
    K[0, 0] = K[1, 1] = focal
    K[0, 2] = w / 2.0
    K[1, 2] = h / 2.0
    return K

# Define a function that calculates the transform of the spectator
class Camera:
    def __init__(self, world, actor, sensor_blueprint_id='sensor.camera.rgb', image_width='800', image_height='600'):
        self.world = world
        self.base_spectator = world.get_spectator()
        self.actor_location = None
        self.actor = actor
        self.radius = 5.0
        self.theta = 0.0
        self.phi = 0.0
        # self.tick()

        # Create a blueprint for the camera
        camera_blueprint = world.get_blueprint_library().find(sensor_blueprint_id)
        camera_blueprint.set_attribute('image_size_x', image_width)
        camera_blueprint.set_attribute('image_size_y', image_height)

        # Get the camera attributes
        camera_initial_transform = carla.Transform(carla.Location(x=0.0, y=0.0, z=0.0))  
        self.camera = world.spawn_actor(camera_blueprint, camera_initial_transform, attach_to=self.base_spectator)

        # Get the attributes from the camera
        self.image_w = camera_blueprint.get_attribute("image_size_x").as_int()
        self.image_h = camera_blueprint.get_attribute("image_size_y").as_int()
        self.fov = camera_blueprint.get_attribute("fov").as_float()
        
        # Calculate the camera projection matrix to project from 3D -> 2D
        self.K = build_projection_matrix(self.image_w, self.image_h, self.fov)

        # Create a queue to store and retrieve the sensor data
        self.image_queue = queue.Queue()
        self.camera.listen(self.image_queue.put)


    def is_in_view(self):
        forward_vec = self.base_spectator.get_transform().get_forward_vector()
        ray = self.actor.get_transform().location - self.base_spectator.get_transform().location
        return forward_vec.dot(ray) > 1
    
    def get_vertices(self):
        verts = [v for v in self.actor.get_bounding_box().get_world_vertices(self.actor.get_transform())]
        return verts

    def get_transform(self):
        return self.camera.get_transform()
    
    def get_matrix(self):
        return np.array(self.get_transform().get_inverse_matrix())

    def get_shape(self):
        return self.camera_blueprint.get_attribute('image_size_x'), self.camera_blueprint.get_attribute('image_size_y')

    def get_image(self):
        while not self.image_queue.empty():
            self.image_queue.get()
        self.world.tick()
        return self.image_queue.get()
    
    def follow(self, actor):
        actor_location = actor.get_location()
        if self.actor_location is not None and self.actor_location == actor_location:
            return
        self.actor_location = actor_location
        self.tick()

    def rotate(self, theta, phi):
        if self.theta == theta and self.phi == phi:
            return
        self.theta = theta
        self.phi = phi
        self.tick()

    def dolly(self, radius):
        if self.radius == radius:
            return
        self.radius = radius
        self.tick()

    def tick(self):

        self.actor_location = self.actor.get_location()

        # Calculate the new location of the spectator
        location = carla.Location()
        location.x = self.actor_location.x + self.radius * math.sin(self.theta) * math.cos(self.phi)
        location.y = self.actor_location.y + self.radius * math.sin(self.theta) * math.sin(self.phi)
        location.z = self.actor_location.z + self.radius * math.cos(self.theta)

        # Calculate the rotation that makes the spectator look at the vehicle
        rotation = carla.Rotation()
        rotation.yaw = math.degrees(self.phi) + 180 # Yaw angle_radian
        rotation.pitch = -math.degrees(math.pi/2 - self.theta)  # Pitch angle_radian

        # Create a new transform with the new location and the new rotation
        spectator_transform = carla.Transform(location, rotation)

        # Get the transform of the camera before the tick
        prev_transform = self.get_transform()

        # Set the new transform to the spectator
        self.base_spectator.set_transform(spectator_transform)
        
        # Wait until the transform is updated
        for _ in range(5):
            self.world.tick()

class Actor:
    def __init__(self, world) -> None:
        self.world = world
        self.base_actor = None
        self.blueprint = None
        self.spawn_point = None
        self.prev_actors = []
        
    def create_actor(self, blueprint, spawn_point):
        # Check if the blueprint and spawn point are the same
        if self.blueprint == blueprint and self.spawn_point == spawn_point:
            return
        self.blueprint = blueprint
        self.spawn_point = spawn_point
        
        # Destroy the previous actor
        if self.base_actor is not None:
            self.base_actor.destroy()
        
        # Spawn the vehicle
        self.base_actor = self.world.spawn_actor(blueprint, spawn_point)
        self.prev_actors.append(self.base_actor)

        # Wait until the actor stop bouncing
        while True:
            prev_location = self.get_location()
            self.world.tick()
            if prev_location == self.get_location():
                break

    def get_transform(self):
        return self.base_actor.get_transform()
    
    def get_location(self):
        return self.base_actor.get_location()
    
    def get_bounding_box(self):
        return self.base_actor.bounding_box

    def __del__(self):
        self.base_actor.destroy()