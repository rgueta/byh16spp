from machine import UART,Timer
import utime
gsm = UART(0,115200)

def simResponse(timer):
    if gsm.any() > 0:
        # response = gsm.readline()
        # print('Straight --> ', response)
        print(str(gsm.readline(), 'utf-8').rstrip('\r\n'))


print('sim monitor init...')
sim800Timer = Timer()

sim800Timer.init(freq=2, mode=Timer.PERIODIC, callback=simResponse)

# Init gsm
gsm.write('AT+CMGF=1\r')
utime.sleep(1)

gsm.write('AT+CNMI=2,2,0,0,0\r')
utime.sleep(1)

