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
apn = 'internet.itelcel.com'
apn_usr = 'webgpr'
apn_pwd = 'webgprs2002'
gsm.write('AT+CSTT="%s","%s","%s"\r' % (apn,apn_usr,apn_pwd))
utime.sleep(1)
gsm.write('AT+SAPBR=3,1,"Contype","GPRS"\r')
utime.sleep(1)
gsm.write('AT+SAPBR=3,1,"APN","%s"\r' % apn)
utime.sleep(1)

gsm.write('AT+CMGF=1\r')
utime.sleep(1)

gsm.write('AT+CNMI=2,2,0,0,0\r')
utime.sleep(1)

