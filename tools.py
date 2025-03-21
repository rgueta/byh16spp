from machine import UART, Pin, Timer, I2C # type: ignore
import utime # type: ignore
from ssd1306_non_rotate import SSD1306_I2C


# --Primarity test using 6k+-1 optimization.
def is_prime(n: int) -> bool:
    if n <= 3:
        return n > 1
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i ** 2 <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def write_i2c(mess):
    i2c = machine.I2C(0, scl=machine.Pin(27), sda=machine.Pin(26), freq=400000) # type: ignore
    while rdy.value() == 0: # type: ignore
        pass
    return i2c.mem_write(mess, 0x74, 0x11)


def read_i2c():
    i2c = machine.I2C(0, scl=machine.Pin(21), sda=machine.Pin(20), freq=400000) # type: ignore
    while rdy.value() == 0: # type: ignore
        pass
    return i2c.mem_read(36, 0x74, 0x01)


def Check_i2c():
    i2c = machine.I2C(0, scl=machine.Pin(21), sda=machine.Pin(20), freq=400000) # type: ignore
    utime.sleep(0.2)
    devices = i2c.scan()

    if len(devices) == 0:
        print("No I2C device found")
    elif len(devices) > 1:
        print("Multiple I2C devices found -")
        for d in devices:
            print("  0x{:02X}".format(d))
    else:
        print("I2C device found at 0x{:02X}".format(devices[0]))
        device = devices[0]


#         ret1 = i2c.writeto(device, b'x3')
#         ret2 = i2c.writeto(device, 2, b'x80')

def gpio(gpio_num, value):
    gpio = Pin(gpio_num, Pin.OUT)
    gpio.value(value)


def append_line_to_file(file_path, lines_to_append):
    try:
        with open(file_path, 'a') as file:
            file.write(lines_to_append + '\n')
    except Exception as e:
        print("Error: ",  {e})



# Check_i2c()
# gpio(26,0)


if __name__ == "__main__" :
     print("Running tools.py locally")
