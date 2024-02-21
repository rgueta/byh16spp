
from machine import UART,Pin, I2C

WIDTH = config['screen']['width']
HEIGHT = config['screen']['height']

# i2c = I2C(0)
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)
oled.fill(0)
