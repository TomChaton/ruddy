from machine import PWM
# NB PWM class works in nanometres

class servo():
    def __init__(self, pin, freq):
        self.pwm = PWM(pin)
        self.pwm.freq(freq)        
    
    def goto(self, degrees):
        # So this part is weird. Without it, you only get 90 degrees of rotation
        # Need to be careful if this is the servo itself, and we get different hardware later on
        degrees = degrees*2
        # from http://www.ee.ic.ac.uk/pcheung/teaching/DE1_EE/stores/sg90_datasheet.pdf
        # 0 = 1.5ms  = 1500000ns
        # 90 = 2.0ms = 2000000ns
        # -90 = 1.0ms  = 1000000ns
        # So according to this: https://forum.arduino.cc/t/convert-angles-to-microseconds/129985/3
        # 90 degrees = 500,000ns
        # therefore 9deg = 50,000ns
        
        ns = int(1500000 + (degrees * 150000 + 13) / 27);
        #print(str(ns/1000000) + 'ms', str(ns) + 'ns')
        self.pwm.duty_ns(ns)
