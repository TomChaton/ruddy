# https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python/blob/master/00-Preface.ipynb
from bmp180 import BMP180

class pressure():
    
    def __init__(self, i2c, oversample):
        self.bmp180 = BMP180(i2c)
        # oversample_setting adjusts the sensor sensitivity 0=lowest/fastest 3=highest/slowest
        self.bmp180.oversample_setting = oversample
        # Set baseline pressure to current pressure to get relative altitude
        self.bmp180.baseline = self.bmp180.pressure
        
    def get_values(self):
        vals = {}
        vals['temperature'] = self.bmp180.temperature
        vals['pressure'] = self.bmp180.pressure
        vals['altitude'] = self.bmp180.altitude
        
        return vals
    
    def get_altitude(self):
        return self.get_values()['altitude']
