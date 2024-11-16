from machine import Pin, PWM
import utime
import json

conf = open('config.json')
config = json.loads(conf.read())
demo = config['app']['demo']
angle = config['pi_pins']['gpio_servo_gate_angle']

if demo:
    close_wait = config['pi_pins']['gpio_servo_gate_delay']
    pwm = PWM(Pin(config['pi_pins']['gpio_servo_gate']))
    pwm.freq(50)


def Init():
    servo16(170)


def Activate():
    if demo:
        #         servo(180)
        #         utime.sleep(close_wait)
        #         servo(0)
        servoSteps1()
    else:
        pin = config['pi_pins']['gpio_gate_door']
        gatePin = Pin(pin, Pin.OUT)

        gatePin.value(0)
        gatePin.value(1)
        utime.sleep(config['pi_pins']['gpio_gate_delay'])
        gatePin.value(0)


def Open():
    print('gate.py Opening.. pin [ ' + str(config['pi_pins']['gpio_servo_gate']) +' ]')
    for degree in range(170, 110, -1):
        if degree == 110:
            utime.sleep(0.06)
        servo16(degree)
        utime.sleep(0.08)


def Close():
    print('Closing.!')
    for degree in range(110, 170, 1):
        if degree == 170:
            utime.sleep(0.06)
        servo16(degree)
        utime.sleep(0.08)


def servo(degrees):
    newDuty = ((int(degrees) + 45) * 100000) / 9
    pwm.duty_ns(int(newDuty))


def servo16(degrees):
    if degrees > 180: degrees = 180
    if degrees < 0: degrees = 0
    maxDuty = 9000
    minDuty = 1000
    newDuty = minDuty + (maxDuty - minDuty) * (degrees / 180)
    pwm.duty_u16(int(newDuty))


def servoSteps():
    for degree in range(0, angle, 1):
        servo(degree)
        utime.sleep(0.05)
    #         print("increasing -- "+str(degree))

    utime.sleep(close_wait)

    for degree in range(angle, 0, -1):
        if degree == 0:
            utime.sleep(0.06)
        servo(degree)
        utime.sleep(0.04)


#         print("decreasing -- "+str(degree))

def servoSteps1():
    Open()
    utime.sleep(close_wait)
    Close()


if __name__ == "__main__":
    # run locally
    print('Hello running gate program locally..')
    #     Activate()
    #     servoSteps()
    Init()
    utime.sleep(5)

    while True:
        Open()
        utime.sleep(5)
        Close()
        utime.sleep(5)


