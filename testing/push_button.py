from machine import Pin
import magnet
import gate
import json

conf = open('config.json')
config = json.loads(conf.read())
conf.close()

push_button = Pin(14, Pin.IN)
led = Pin(25, Pin.OUT)

print('push button')

while True:
    if push_button.value() == True:
        led.value(1)
        gate.Activate()
    else:
        led.value(0)

