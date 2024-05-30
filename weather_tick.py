import math

class Sun(object):
    def __init__(self, weather):
        self.weather = weather
        self._t = 0.0
        self.azimuth = weather.sun_azimuth_angle

    def tick(self, delta_seconds):
        self._t += 0.008 * delta_seconds
        self._t %= 2.0 * math.pi
        self.azimuth += 0.25 * delta_seconds
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

    def tick(self, delta_seconds):
        delta = (1.3 if self._increasing else -1.3) * delta_seconds
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

    def tick(self, delta_seconds):
        self.sun.tick(delta_seconds)
        self.storm.tick(delta_seconds)

    def __str__(self):
        return '%s %s' % (self._sun, self._storm)