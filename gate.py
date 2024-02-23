from machine import Pin, PWM
import utime
import json

conf = open('config.json')
config = json.loads(conf.read())
demo = config['app']['demo']
angle = config['pi_pins']['gpio_servo_gate_angle']
pin_gate = config['pi_pins']['gpio_servo_gate']
close_wait = config['pi_pins']['gpio_servo_gate_delay']

if demo:
    pwm = PWM(Pin(pin_gate))
    pwm.freq(50)
else:
    pin = config['pi_pins']['gpio_gate_door']
    gatePin = Pin(pin, Pin.OUT)
    gatePin.value(0)

def Activate():
    if demo:
        servoSteps1()
    else:
        pin = config['pi_pins']['gpio_gate_door']
        gatePin = Pin(pin, Pin.OUT)

        gatePin.value(0)
        gatePin.value(1)
        utime.sleep(config['pi_pins']['gpio_gate_delay'])
        gatePin.value(0)

def rotate(position):
    pwm.duty_u16(position)
    utime.sleep(0.01)

def Open():
    for pos in range(9000, 6500, -10):
        rotate(pos)

def Close():
    for pos in range(6500, 9000, 10):
        rotate(pos)

def servoSteps1():
    Open()
    if demo:
        print('Si esta en modo demo..')
        utime.sleep(close_wait)
        Close()

if __name__ == "__main__":
    # run locally
    print('Hello running gate program locally..')

    acc = 0
    while True:
        servoSteps1()
        acc+=1
        if acc == 3:
            print('Finish')
            break
