#https://github.com/adamjezek98/MPU6050-ESP8266-MicroPython
#https://github.com/micropython-IMU/micropython-fusion
import mpu6050
import time

class accelerometer():
    
    def __init__(self, i2c, addr=0x68):
        self.mpu6050 = mpu6050.accel(i2c)
        self.AXoff = 0
        self.AYoff = 0
        self.AZoff = 0
    
        self.GXoff = 0
        self.GYoff = 0
        self.GZoff = 0
        
        self.gSensitivity = 16384
        self.degreeSec    = 131.07
        
    def calibrate(self):       
        avgs = {}
        avgs['AX'] = []
        avgs['AY'] = []
        avgs['AZ'] = []
        avgs['GX'] = []
        avgs['GY'] = []
        avgs['GZ'] = []
        
        samples = 20;
        
        for x in range(samples):
            raw = self.mpu6050.get_values()
            avgs['AX'].append(raw['AcX'])
            avgs['AY'].append(raw['AcY'])
            avgs['AZ'].append(raw['AcZ'])
            avgs['GX'].append(raw['GyX'])
            avgs['GY'].append(raw['GyY'])
            avgs['GZ'].append(raw['GyZ'])
            time.sleep(0.5)
        
            
        self.AXoff = sum(avgs['AX']) / samples
        self.AYoff = sum(avgs['AY']) / samples
        self.AZoff = sum(avgs['AZ']) / samples
        
        self.GXoff = sum(avgs['GX']) / samples
        self.GYoff = sum(avgs['GY']) / samples
        self.GZoff = sum(avgs['GY']) / samples
        
    def get_offsets(self):
        vals = {}
        vals['AXoff'] = self.AXoff
        vals['AYoff'] = self.AYoff
        vals['AZoff'] = self.AZoff
        
        vals['GXoff'] = self.GXoff
        vals['GYoff'] = self.GYoff
        vals['GZoff'] = self.GZoff               
        
        return vals
    
    def get_values(self):
        raw = self.mpu6050.get_values()
        vals = {}
        vals['AcX'] = (raw['AcX'] - self.AXoff) / self.gSensitivity
        vals['AcY'] = (raw['AcY'] - self.AYoff) / self.gSensitivity
        vals['AcZ'] = (raw['AcZ'] - self.AZoff - self.gSensitivity) / self.gSensitivity
        
        vals['GyX'] = (raw['GyX'] - self.GXoff) / self.degreeSec
        vals['GyY'] = (raw['GyY'] - self.GYoff) / self.degreeSec
        vals['GyZ'] = (raw['GyZ'] - self.GZoff) / self.degreeSec
        
        return vals
    
    def get_acz(self):
        return self.get_values()['AcZ'] + 1
        
