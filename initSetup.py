from machine import Pin, Timer
import utime
import json
conf = open('config.json')
config = json.loads(conf.read())


if "__name__" == "__main__":
    #run locally
    print()

def Initial():
    print('initSetup..')
    magnetPin = Pin(config['pi_pins']['gpio_magnet'], Pin.OUT)
    gatePin = Pin(config['pi_pins']['gpio_gate_door'], Pin.OUT)
    magnetPin.value(0)
    gatePin.value(0)


