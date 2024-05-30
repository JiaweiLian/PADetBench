import math
import carla

def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(value, maximum))

class Sun(object):
    def __init__(self, weather):
        self.weather = weather
        self._t = 0.0
        self.azimuth = weather.sun_azimuth_angle

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
        self._t = weather.precipitation if weather.precipitation > 0.0 else -50.0
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
    def __init__(self, weather):
        self.weather = weather
        self.sun = Sun(weather)
        self.storm = Storm(weather)

    def tick(self, delta):
        self.sun.tick(delta)
        self.storm.tick(delta)

    def __str__(self):
        return '%s %s' % (self.sun, self.storm)

# Define a function that calculates the transform of the spectator
class Spectator:
    def __init__(self, vehicle, radius, height):
        self.vehicle = vehicle
        self.radius = radius
        self.height = height
        self.angle_radian = 0.0

    def tick(self, speed_rotation_degree):
        # Update the angle of the spectator
        self.angle_radian = 0

        # Get the location of the vehicle
        vehicle_location = self.vehicle.get_location()

        # Calculate the new location of the spectator
        location = carla.Location()
        location.x = vehicle_location.x + self.radius * math.cos(self.angle_radian)  # X-coordinate
        location.y = vehicle_location.y + self.radius * math.sin(self.angle_radian)  # Y-coordinate
        location.z = vehicle_location.z + self.height                    # Z-coordinate

        # Calculate the rotation that makes the spectator look at the vehicle
        rotation = carla.Rotation()
        rotation.yaw = math.degrees(self.angle_radian) + 180 # Yaw angle_radian
        rotation.pitch = -math.degrees(math.atan(self.height / self.radius))  # Pitch angle_radian

        # Create a new transform with the new location and the new rotation
        transform = carla.Transform(location, rotation)
