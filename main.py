from machine import SoftI2C, SPI, Pin, disable_irq, enable_irq
import time, math, utime, _thread, gc
# https://micropython-ulab.readthedocs.io/en/latest/index.html
from ulab import numpy as np
from accelerometer import accelerometer
from logger import logger
from pressure import pressure
from servo import servo
from switch import switch
from rgb_led import RGBLED

MODE_INIT              = 1 # able to pack parachute, remove fairing etc.
MODE_LAUNCH_DETECT     = 2 # fairing locked
MODE_FLIGHT            = 3 # start logging to sd card
MODE_MAIN_CHUTE_DEPLOY = 4 # parachute 
current_mode = MODE_INIT

SPI_SCK_PIN  = 2
SPI_MOSI_PIN = 3
SPI_MISO_PIN = 0
SPI_CS_PIN   = 1

I2C_SDA_PIN  = 6
I2C_SCL_PIN  = 7
I2C_FREQ     = 400000

ALTIMETER_SENSITIVITY = 3
WINDOW_SIZE = 10

SERVO_PIN          = 5
SERVO_FREQ         = 50
SERVO_MODE_POS_MAP = {}
SERVO_MODE_POS_MAP[MODE_INIT]              = 30
SERVO_MODE_POS_MAP[MODE_LAUNCH_DETECT]     = 60
SERVO_MODE_POS_MAP[MODE_FLIGHT]            = 60
SERVO_MODE_POS_MAP[MODE_MAIN_CHUTE_DEPLOY] = 90

BUTTON_PIN = 4

RED_PIN   = 29
GREEN_PIN = 28
BLUE_PIN  = 27

# Initialise led
led = RGBLED(RED_PIN, GREEN_PIN, BLUE_PIN, False)
orange = 0xFF3000
red    = 0xFF0000
green  = 0x00FF00
LED_MODE_FLASH = 'flash'
LED_MODE_SOLID = 'solid'
ledColour = orange
ledMode   = LED_MODE_FLASH
terminate = False
buzzer = machine.PWM(Pin(26, Pin.OUT))
buzzer.freq(300)

def second_thread():
    global current_mode
    global ledColour
    global ledMode
    global terminate
    global buzzer
    
    while True:
        if terminate == True:
            break
        if ledMode == LED_MODE_SOLID:
            led.setColor(ledColour)
        else:
            for i in range(0, current_mode):
                led.setColor(ledColour)
                buzzer.duty_u16(1000)
                utime.sleep(0.3)
                buzzer.duty_u16(0)
                led.off()
                utime.sleep(0.3)
        utime.sleep(1.25)
            
_thread.start_new_thread(second_thread, ())

# Initialize sd card
logger_spi = SPI(0, sck = Pin(SPI_SCK_PIN, Pin.OUT), mosi = Pin(SPI_MOSI_PIN), miso = Pin(SPI_MISO_PIN))
log = logger(logger_spi, Pin(SPI_CS_PIN))

# Address the i2c bus
i2c = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# Initialise accelerometer
accel = accelerometer(i2c)
accel.calibrate()

# Initialise the pressure sensor
altimeter = pressure(i2c, ALTIMETER_SENSITIVITY)

# Initialise the release mechanism
release_mechanism = servo(Pin(SERVO_PIN), SERVO_FREQ)
release_mechanism.goto(SERVO_MODE_POS_MAP[current_mode])

# Initialise button
switch_pin = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
my_switch = switch(switch_pin, 2)

# Initialise the datasets
altitude_dataset     = []
acceleration_dataset = []
launch_detect = 0
apogee_detect = 0
for i in range(WINDOW_SIZE):
    acceleration_dataset.append(accel.get_acz())
    altitude_dataset.append(altimeter.get_altitude())
    
# turn led green if all the above is fine.
ledColour = green
buzzer.freq(400)

def goto_mode(mode=None):
    global current_mode
    global launch_detect
    global apogee_detect
    if mode is not None:
        current_mode = mode
    else:
        if current_mode == MODE_MAIN_CHUTE_DEPLOY:
            current_mode = MODE_INIT
            launch_detect = 0
            apogee_detect = 0
        else:
            current_mode = current_mode + 1
        
    release_mechanism.goto(SERVO_MODE_POS_MAP[current_mode])


def exponential_moving_average(values, window):
    gc.collect() 
    np_values = np.array(values)
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= np.sum(weights)
    
    a = np.convolve(np_values, weights)[:len(np_values)]
    #a[:window]=a[window]
    
    return a

def log_data(accel, altimeter, av_accel, av_alt, launch_detect, apogee_detect, mode):
    global log
    # do a thing
    acceleration_data = [accel['AcX'], accel['AcY'], accel['AcZ'], accel['GyX'], accel['GyY'], accel['GyZ']]
    altimeter_data    = [altimeter['temperature'], altimeter['pressure'], altimeter['altitude']]
    log_line = []
    log_line[len(log_line):] = acceleration_data
    log_line[len(log_line):] = altimeter_data
    log_line[len(log_line):] = [av_accel, av_alt, launch_detect >= 1, apogee_detect >= 1, mode]
    log.write_line(log_line)

launch_detect = 0
apogee_detect = 0
# main loop
while True:
    my_switch_new_value = False

    # Disable interrupts for a short time to read shared variable
    irq_state = disable_irq()
    if my_switch.new_value_available:
        my_switch_value = my_switch.value
        my_switch_new_value = True
        my_switch.new_value_available = False
    enable_irq(irq_state)

    # If my switch had a new value, print the new state
    if my_switch_new_value:
        if not my_switch_value:
            goto_mode()
            continue

    altimeter_data     = altimeter.get_values()
    new_alt            = altimeter_data['altitude']
    new_average_alt    = exponential_moving_average(altitude_dataset, WINDOW_SIZE-1)
    altitude_dataset.append(new_alt)
    altitude_dataset.pop(0)
    
    accelerometer_data = accel.get_values()
    new_accel          = accelerometer_data['AcX']
    new_average_accel  = exponential_moving_average(acceleration_dataset, WINDOW_SIZE-1)
    acceleration_dataset.append(new_accel)
    acceleration_dataset.pop(0)
    
    if current_mode == MODE_LAUNCH_DETECT:
        if new_accel > new_average_accel[-1]:
            launch_detect += 0.05
        else:
            launch_detect = 0
        
        if launch_detect >= 1:
            goto_mode(MODE_FLIGHT)
            
    if current_mode == MODE_FLIGHT:
        log_data(accelerometer_data, altimeter_data, new_average_accel[-1], new_average_alt[-1], launch_detect, apogee_detect, current_mode)
        if new_alt < new_average_alt[-1]:
            apogee_detect += 0.055
        else:
            apogee_detect = 0
            
        if apogee_detect >= 1:
            goto_mode(MODE_MAIN_CHUTE_DEPLOY)
        
    if current_mode == MODE_MAIN_CHUTE_DEPLOY:
        log_data(accelerometer_data, altimeter_data, new_average_accel[-1], new_average_alt[-1], launch_detect, apogee_detect, current_mode)
