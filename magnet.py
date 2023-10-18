from machine import Pin, PWM
import utime
import json

conf = open('config.json')
config = json.loads(conf.read())
demo = config['app']['demo']
angle = config['pi_pins']['gpio_servo_magnet_angle']

if demo:
    close_wait = config['pi_pins']['gpio_servo_magnet_delay']
    pwm = PWM(Pin(config['pi_pins']['gpio_servo_magnet']))
    pwm.freq(50)
else:
    pin = config['pi_pins']['gpio_magnet']
    print('Activating magnet..pin --> ', pin)
    magnetPin = Pin(pin, Pin.OUT)
    
    magnetPin.value(0)
    magnetPin.value(1)
    utime.sleep(config['pi_pins']['gpio_magnet_delay'])
    magnetPin.value(0)

def Activate():
    if demo:
        servoSteps1()
    else:
        pin = config['pi_pins']['gpio_magnet']
        magnetPin = Pin(pin, Pin.OUT)

        magnetPin.value(0)
        magnetPin.value(1)
        utime.sleep(config['pi_pins']['gpio_magnet_delay'])
        magnetPin.value(0)

def rotate(position):
    pwm.duty_u16(position)
    utime.sleep(0.01)

def Open():
    for degree in range(3000, 5500, 10):
        rotate(degree)

def Close():
    for degree in range(5500, 3000, -10):
        rotate(degree)

def servoSteps1():
    Open()
    if demo:
        print('Si esta en modo demo..')
        utime.sleep(close_wait)
        Close()

if __name__ == "__main__":
    # run locally
    print('Hello running magnet program locally..')

    acc = 0
    while True:
        servoSteps1()
        acc+=1
        if acc == 3:
            print('Finish')
            break
