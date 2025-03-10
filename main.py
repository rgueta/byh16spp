from micropython import * # type: ignore
from machine import UART, Pin, I2C, Timer, RTC, ADC, PWM, reset, soft_reset # type: ignore
import uos # type: ignore
import gc
import json
import utime # type: ignore
import magnet
import gate
import initSetup
import jsonTools
import math

import tools


# region Memory status  ----------------------

def diskUsage(send = False):
    s = uos.statvfs('/')
    print(s)
    U = s[0]*s[3]/1024
    T = s[0]*s[2]/1024
    P = '{0:.2f}%'.format(((T - U ) * 100) / T)
    msg = 'Disk space: {0} Kb free space out of {1} Kb ({2} in use)'.format(U, T, P)
    if debugging:
        print(msg)

    if send:
        return msg 

def memUsage(send = False):
    gc.collect()
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F + A
    P = '{0:.2f}%'.format(100-F/T*100)
    msg = 'Ram memory: {0:.2f} Kb free out of {1:.2f} Kb ({2} in use)'.format(F/1024, T/1024, P)

    if debugging:
        print(msg)

    if send:
        return msg 

        return get_dir_size(path)

# endregion   -----------------------------

# region -------- json file config, events, restraint  ------------------


conf = open('config.json')
config = json.loads(conf.read())
conf.close()

rotate_display = config['app']['rotate']
if rotate_display:
    from ssd1306_rotate import SSD1306_I2C
    print('rotate display------------------')
else:
    from ssd1306_non_rotate import SSD1306_I2C
    print('non rotate display------------------')

restraint = open('restraint.json')
restraint_list = json.loads(restraint.read())
restraint.close()

# endregion ----------------


# region ------     Variables     ------------------

demo = config['app']['demo']
debugging = config['app']['debugging']
Exceptions = ''
timestamp = ''
tupleToday = ()
emptyTuple = ()
Today = ''
gsm_status = []
sendStatus = False
active_codes = {"codes": []}
coreId = config['app']['coreId']
show_code = config['app']['show_code']
buzzer_pin = config['pi_pins']['buzzer']
version_app = config['app']['version']
openByCode = config['app']['openByCode']
_settingsCode = config['app']['settingsCode']
pwdRST = config['app']['pwdRST']
settingsMode = False
settingsCode = ''
readyToConfig = False
cmdLineTitle= 'Codigo:             '
code = ''
screen_saver = 0

# ----- Intialization -----------
buzzer = PWM(Pin(buzzer_pin))
if debugging:
    print('Version ' + version_app)

# wait until gsm device connect to network
utime.sleep(14)
initSetup.Initial()

# ------------------ Setup GSM -----------------------
gsm_tx = config['pi_pins']['gsm_TX']
gsm_rx = config['pi_pins']['gsm_RX']
gsm_baud = config['sim']['serial_baud']
encoding = 'utf-8'
# gsm = UART(0, 9600, tx=Pin(gsm_tx), rx=Pin(gsm_rx), rxbuf=512)
gsm = UART(0, gsm_baud, tx=Pin(gsm_tx), rx=Pin(gsm_rx))

# ------------------ Setup NFC -----------------------
nfc_baud = config['nfc']['serial_baud']
nfc_tx = config['nfc']['nfc_TX']
nfc_rx = config['nfc']['nfc_RX']
nfc = UART(1, nfc_baud, tx=Pin(nfc_tx), rx=Pin(nfc_rx))
lastTag = 0

# Setup codes json file
code_list = {}


# region   -----Time Zone  --------------------
timeZone = config['app']['timeZone']
datatimeFormat = config['app']['dateTimeFormat']
# now_utc = datetime.now(timezone(timeZone))
# current_time = now_utc.strftime(datatimeFormat)

# endregion ---------------------------------

# region -------- Display  ----------------------
code_hide_mark = config['screen']['code_hide_mark']

scl1 = config['pi_pins']['gpio_oled_scl1']
sda1 = config['pi_pins']['gpio_oled_sda1']
# scl2 = config['pi_pins']['gpio_oled_scl2']
# sda2 = config['pi_pins']['gpio_oled_sda2']

WIDTH = config['screen']['width']
HEIGHT = config['screen']['height']

i2c1 = I2C(1, scl=Pin(scl1), sda=Pin(sda1), freq=400000)

oled1 = SSD1306_I2C(WIDTH, HEIGHT, i2c1)
if rotate_display:
    oled1.rotate(2)

# endregion -------------------------------------------------------

# region ------------- Key pad gpio setup  ----------------------------
KEY_UP = const(0) # type: ignore
KEY_DOWN = const(1) # type: ignore

MATRIX = config['keypad_matrix'][config['keypad_matrix']['default']]
ROWS = config['pi_pins']['keypad_rows']
COLS = config['pi_pins']['keypad_cols']

row_pins = [Pin(pin_name, mode=Pin.OUT) for pin_name in ROWS]
col_pins = [Pin(pin_name, pull=Pin.PULL_DOWN) for pin_name in COLS]

# endregion -----------------------------------------

# region ------------ SIM800L  -----------------------

sendCodeEvents = config['sim']['sendCodeEvents']
admin_sim = config['app']['admin_sim'].split(',')
apn = config['sim']['apn']
serial_port = config['sim']['serial_port']
serial_baud = config['sim']['serial_baud']
serial_timeout = config['sim']['serial_timeout']
HTTPACTION_waitTime = config['sim']['HTTPACTION_waitTime']
api_get_line = config['sim']['api_get_line']
incoming_calls = config['sim']['incoming_calls']


# region -------- Configuration  -------------------------------------

def changeSetting(value):
    global MATRIX
    global sendStatus
    applied = False

    # keypad  -----------------------------------
    if value == '00': # reboot
        oled1.fill(0)
        printHeaderSettings()
        oled1.text('Booting.. ', 1, 22)
        oled1.show()
        utime.sleep(3)
        softReset()
        applied = True

    elif value == '01': # get Sim Info
        getSimInfo()
        applied = True

    elif value == '02': # get timestamp
        updTimestamp()
        applied = True

    elif value == '03': # get phone number
        sendStatus = True
        getPhoneNum()
        applied = True

    elif value == '1': # set matrix for flex keypad
        MATRIX = config['keypad_matrix']['flex']
        applied = True

    elif value == '2': # set matrix for hard plastic keypad
        MATRIX = config['keypad_matrix']['hardPlastic']
        applied = True

    # debug -----------------------------------
    elif value == '10':  #debug true
        jsonTools.updJson('u','config.json','app', 'debugging', True)
        applied = True

    elif value == '11': #debug false
        jsonTools.updJson('u','config.json','app', 'debugging', False)
        applied = True

    # Opening locally--------------------------------------
    elif value == '20': # Open Gate
        gate.Activate()
        applied - True

    elif value == '21': # Open Gate
        magnet.Activate()
        applied - True

    return applied
    
# endregion

# initial gprs configuration
# def gsm_config_gprs():
#     print(" --- CONFIG GPRS --- ");
#     gsm.write('AT+SAPBR=3,1,"Contype","GPRS"\r\n')
#     utime.sleep(1)
#
#     # global keepMonitorSIM800L
#     instr = 'AT+SAPBR=3,1,"APN","%s"\r\n' % apn
#     gsm.write(instr.encode())
#     utime.sleep(1)

# endregion  -------------------------------------

def signal_Status(titulo):
    global gsm_status
    gsm_status = []
    gsm_status.append({'Event':titulo})
    gsm.write('AT+CSQ\r')
    utime.sleep(0.7)
    gsm.write('AT+CBC\r')
    utime.sleep(0.7)

    if debugging:
        print('signal_Status done..')
# endregion  -----------------  Variable  ---------------------------


def str_to_bool(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False

# region ----------  show on display ------------------


def DisplayMsg(msg,time=3):
    global WIDTH
    len_char = int(WIDTH / 8)
    oled1.fill(0)
    oled1.show()
    lines = 1
    if len(msg) > len_char:
        lines = int(len(msg) / len_char)
        if (math.fmod(len(msg),len_char) > 0):
            lines += 1
        for line in range(0, lines):
            oled1.text(msg[(line * len_char) : (len_char * (line + 1)) ] ,0 , line * 8 )
        oled1.show()
    utime.sleep(time)

def showMsg(msg):
    oled1.fill(0)
    oled1.show()
    oled1.text(msg, 1, 0)
    oled1.show()
    utime.sleep(0.9)
    oled1.text(msg + '.', 1, 0)
    oled1.show()
    utime.sleep(0.9)
    oled1.text(msg + '..', 1, 0)
    oled1.show()
    utime.sleep(0.9)
    oled1.text(msg + '...', 1, 0)
    oled1.show()
    utime.sleep(0.9)
    ShowMainFrame()

def showVersion(msg):
    oled1.fill(0)
    # oled1.show()
    oled1.text(msg, 1, 0)
    oled1.show()
    utime.sleep(0.9)
    oled1.text(msg + '.', 1, 0)
    oled1.show()
    utime.sleep(0.9)
    oled1.text(msg + '..', 1, 0)
    oled1.show()
    utime.sleep(0.9)
    oled1.text(msg + '...', 1, 0)
    oled1.show()
    utime.sleep(3)

def screenSaver():
    oled1.fill(0)
    oled1.show()

def printHeader():
    oled1.fill(0)
    oled1.text("* <-", 1, 0)
    oled1.text(Today[-2:], 45, 0)
    oled1.text('# enter', 75, 0)
    if len(active_codes['codes']) > 0:
        oled1.text(str(len(active_codes['codes']))+'', 1, 9)

def printHeaderSettings():
    oled1.fill(0)
    oled1.text("* <-", 1, 0)
    oled1.text(Today[-2:], 45, 0)
    oled1.text('config', 1, 9)
    oled1.text('# enter', 75, 0)
    oled1.show()

def ShowMainFrame():
    global screen_saver
    oled1.fill(0)
    oled1.text("* <-", 1, 0)
    oled1.text(Today[-2:], 45, 0)
    oled1.text('# enter', 75, 0)
    if len(active_codes['codes']) > 0:
        oled1.text(str(len(active_codes['codes']))+'', 1, 9)
    oled1.text("Codigo: ", 1, 22)
    oled1.show()
    screen_saver = 0

# endregion  ----------------------


'''
 ------------------------------------------
 function to send data to server
 option : 1 = json type, 2 = string type
 data   : data to send 
 lenght : lenght parameter required for POST   
 url    : API url address
 ------------------------------------------

'''
def postData(type = 1, data = any,lenght = 0, url = ''):
    strData = ''

    if type == 1:
        strData = json.dumps(data) + '\r'

    elif type == 2:
        strData = data + '\r'

    try:
        
        gsm.write('AT+HTTPSSL=0\r\n')
        utime.sleep(1)

        gsm.write('AT+HTTPTERM\r')
        utime.sleep(1)

        gsm.write('AT+SAPBR=1,1\r')
        utime.sleep(2)

        gsm.write('AT+SAPBR=2,1\r')
        utime.sleep(2)

        gsm.write('AT+HTTPINIT\r')
        utime.sleep(2)

        gsm.write('AT+HTTPPARA="CID",1\r')
        utime.sleep(2)

        gsm.write('AT+HTTPPARA="URL","%s"\r' % url)
        utime.sleep(2)

        gsm.write('AT+HTTPPARA="CONTENT","application/json"\r')
        utime.sleep(2)


        gsm.write('AT+HTTPDATA=%s,5000\r' % str(lenght))
        utime.sleep(1.5)

        gsm.write(strData)
        utime.sleep(3.5)

        # 0 = GET, 1 = POST, 2 = HEAD
        gsm.write('AT+HTTPACTION=1\r')
        utime.sleep(5)

        gsm.write('AT+HTTPREAD\r')
        utime.sleep(2)

        gsm.write('AT+HTTPTERM\r')
        utime.sleep(1)

        gsm.write('AT+SAPBR=0,1\r')
        utime.sleep(4)

       

    except OSError:  # Open failed
        print('Error--> ', OSError)

def correctTime(timestamp):
    OkTime = False
    if(len(timestamp) > 0):
        now = utime.time()
        tspkg = 0
        tspkg = int(timestamp[:10])
        diff = now - tspkg
                
        if (diff < 90 and diff > 0):
            OkTime = True
    
    return OkTime


def updTimestamp():
    gsm.write('AT+CCLK?\r')
    # cleanup expired codes
    utime.sleep(5)    

def initial():
    showVersion('ver. ' + version_app)
    utime.sleep(3)
    global sendStatus
    gsm.write('AT+CCLK?\r')
    # cleanup expired codes
    utime.sleep(6)

    cleanCodes(1, '')
    utime.sleep(2)
    ShowMainFrame()
    # gsm_config_gprs()

    # send module status  ---------------
    sendStatus = True
    signal_Status('Reboot')
    
    # scree saver    -------------------
    utime.sleep(5)
    printHeader()

    if debugging:
        print('initial done..')

def init_gsm():
    # gsm.write('ATE0\r')    # Disable the Echo
    # utime.sleep(0.5)
    apn_usr = config['sim']['APN_USER']
    apn_pwd = config['sim']['APN_PWD']
    gsm.write('AT+CSTT="%s","%s","%s"\r' % (apn,apn_usr,apn_pwd))
    utime.sleep(1)
    gsm.write('AT+SAPBR=3,1,"Contype","GPRS"\r')
    utime.sleep(1)
    gsm.write('AT+SAPBR=3,1,"APN","%s"\r' % apn)
    utime.sleep(1)

    gsm.write('AT+CMGF=1\r')  # Select Message format as Text mode
    utime.sleep(1)
    gsm.write('AT+CNMI=2,2,0,0,0\r')  # New live SMS Message Indications
    utime.sleep(1)

    # gsm.write('AT+CGATT?\r\n')
    # utime.sleep(1)

    if(not incoming_calls):
        gsm.write('AT+GSMBUSY=1\r')
        utime.sleep(1)

    if debugging:
        print('init_gsm done..')

def getSimInfo():
    gsm.write('AT+CCID\r')
    utime.sleep(2)

def getPhoneNum():
    # gsm.write('AT+CNUM\r')
    gsm.write('AT+CSIM\r')
    utime.sleep(2)

def softReset():
    showMsg('Rebooting')
    utime.sleep(1)
    try:
        reset()
    except SystemExit:
        print('Error SystemExit')
        raise SystemExit
        
    except Exception as e:
        print('Error Exception: ', e)
        raise
    
    except:
        print('Error Fallback')
        soft_reset()

def tone(pin, frequency, duration):
    pin.freq(frequency)
    pin.duty_u16(50000)  # volume
    utime.sleep_ms(duration)
    pin.duty_u16(0)


def song(name):
    if name == 'initial':
        tone(buzzer, 1440, 300)
        tone(buzzer, 1150, 300)
        tone(buzzer, 1440, 300)
    elif name == 'fail':
        tone(buzzer, 100, 500)
    elif name == 'ok':
        tone(buzzer, 1100, 200)
        tone(buzzer, 1500, 200)


def InitKeypad():
    for row in range(0, 4):
        for col in range(0, 4):
            row_pins[row].low()

    if debugging:
        print('InitKeypad done..')

def tupleDateFROM_ISO(d):  # get just date from ISO datetime format '2022-01-05T10:53:13.00'
    tPosition = d.index('T')
    onlyDate = d[0:tPosition].split('-')
    tupleDate = (int(onlyDate[0][2:]), int(onlyDate[1]), int(onlyDate[2]))
    return tupleDate


def daysBetween(d1, d2):
    d1 += (1, 0, 0, 0, 0)  # ensure a time past midnight
    d2 += (1, 0, 0, 0, 0)
    return utime.mktime(d1) // (24 * 3600) - utime.mktime(d2) // (24 * 3600)

'''
 -------------------------
 Convert date to human format 
 option : date type options
 date : date package
 -------------------------
'''
def toHumanDate(option = 1, date = any):
    # option 1 format (2025, 1, 1, 13, 14, 35, 2, 1) (YYYY, M, D, hh, mm, ss, weekday, yearday)
    # option 2 format (2025, 1, 1, 3, 13, 14, 35, 1) (YYYY, M, D, weekday, hh, mm, ss, yearday)
    dateH = ''
    if option == 1:
        dateH = str(date[0]) + '-' + str(date[1]) + '-' + str(date[2]) + 'T' + str(date[3]) + ':' + str(date[4]) + ':' + str(date[5])
    
    if option == 2:
        dateH = str(date[0]) + '-' + str(date[1]) + '-' + str(date[2]) + 'T' + str(date[4]) + ':' + str(date[5]) + ':' + str(date[6])

    return dateH

# region -----------  codes  --------------------
# ---  1 : by date, 2 : by duplicity
def cleanCodes(type, code):
    global rtc
    global active_codes
    active_codes = {"codes": []}

    now = utime.time() / 86400  # create timestamp from rtc local
    # now = int(utime.mktime(rtc.datetime()))
    jcodes = open('codes.json')
    code_list = json.loads(jcodes.read())
    jcodes.close()

    for i, item in enumerate(code_list['codes']):
        if type == 1:
            dtcode = (utime.mktime((2000 + int(item['date'][2:4]), int(item['date'][5:7]),
                                  int(item['date'][8:10]), int(item['date'][11:13]),
                                  int(item['date'][14:16]), int(item['date'][17:19]),
                                  0,0))) / 86400  # type: ignore

            if dtcode < now :
                if debugging:
                    print('Code deleted ----> ', item['code'])
            else:
                active_codes['codes'].append(item)

        elif type == 2:
            if code == item['code']:
                del code_list['codes'][i]
                f = open("codes.json", "w")
                json.dump(code_list, f)
                f.close()
                break
    f = open("codes.json", "w")
    json.dump(active_codes, f)
    f.close()
    ShowMainFrame()

    if debugging:
        print('cleanCodes done..')


def verifyCode(cap_code):
    global active_codes
    global code
    for i, item in enumerate(active_codes['codes']):
        if cap_code == item['code']:
            song('ok')
            ShowMainFrame()
            code=''
            if openByCode == 'magnet':
                magnet.Activate()
            elif openByCode == 'gate':
                gate.Activate()
            if sendCodeEvents:
                # reg_code_event(str(item['codeId']))
                # reg_code_event(cap_code)
                reg_code_event(str(item['codeId']))
                if debugging:
                    print('Calling API to store code event')
            else:
                event_pkg = {"code" :cap_code,"codeId":str(item['codeId']),"picId":"NA",
                             "CoreSim":config['sim']['value'],"date":
                             toHumanDate(2,rtc.datetime())}

                jsonTools.updJson('c','events.json','events','', event_pkg)

                if debugging:
                    print('event register locally')

            break

        elif i + 1 == len(active_codes['codes']):
            global warning_message_active
            print('codigo no valido!')
            warning_message_active = True
            song('fail')
            ShowMainFrame()
            code = ''
            

def reg_code_event(code_id):
    data = {"codeId": code_id, "picId": "NA", "CoreSim": config['sim']['value']}
    url = config['sim']['url'] + config['sim']['api_codes_events']
    jsonLen = len(str(data).encode('utf-8'))

    postData(1, data, jsonLen, url)




def reg_local_event(pkg):
    jsonTools.updJson('c','events.json','events','', pkg)


def sendCodeToVisitor(code, visitorSim):
    #  --- send status  -------
    gsm.write('AT+CMGS="' + str(visitorSim, encoding) + '"\r')
    utime.sleep(0.5)
    gsm.write('Codigo de acceso: ' + code + "\r")
    utime.sleep(0.5)
    gsm.write(chr(26))
    utime.sleep(0.5)

# endregion --------  codes --------------------------------

# region current status --------------------------------------------
def uploadCurrentStatus(info):
    global coreId
    data = any
    jsonLen = 0
    url = config['sim']['url'] + config['sim']['api_currentStatus'] + '/'
    key = ''

    if info == 'restraint':
        key = 'user'
        url = url + 'restraint/' + coreId
        res = open('restraint.json')
        data = json.loads(res.read())
        res.close()

    elif info == 'codes':
        key = 'codes'
        url = url + 'codes/' + coreId
        res = open('codes.json')
        data = json.loads(res.read())
        res.close()

    elif info == 'events':
        key = 'events'
        url = url + 'events/' + coreId
        res = open('events.json')
        data = json.loads(res.read())
        res.close()

    elif info == 'extrange':
        key = 'events'
        url = url + 'extrange/' + coreId
        res = open('extrange.json')
        data = json.loads(res.read())
        res.close()

    if len(data[key])> 0:
        jsonLen = len(str(data[key]).encode('utf-8'))
        postData(1, data[key], jsonLen, url)

        if info == 'events' or info == 'extrange':
            file = info + '.json'
             # clear events -----------------------------
            jsonTools.updJson('d',file,'events','', '')

            eve = open(file)
            events = json.loads(eve.read())

            if info == 'events':
                if debugging:
                    print('after cleared lenght events: ', len(events['events']))
            elif info == 'extrange':
                if debugging:
                    print('after cleared lenght extrange: ', len(events['events']))

            eve.close()
            del events
    else:
        if debugging:
            print('No ' + info)
            showMsg('No ' + info)
    
# endregion --------------------------------------------------

# region ------ Timers  -----------------------------------

def tick25(timer):
    global led25
    led25.toggle()

def PollKeypad(timer):
    key = None
    global code
    global code_hide
    global settingsMode
    global readyToConfig
    global settingsCode
    global screen_saver
    for row in range(4):
        for col in range(4):
            row_pins[row].high()
            # Set the current row to high
            row_pins[row].high()
            # Check for key pressed events
            if col_pins[col].value() == KEY_DOWN:
                key = KEY_DOWN
            if col_pins[col].value() == KEY_UP:
                key = KEY_UP
            row_pins[row].low()
            if key == KEY_DOWN:
                # Screen wakeup,screen On  ---------------------------------------
                screen_saver = 0
                printHeader()
                if MATRIX[row][col] == '*':
                    if len(code) > 0:
                        code = code[0:-1]
                        code_hide = code_hide[0:-1]
                # region keypad # option -----------------
                elif MATRIX[row][col] == '#':
                    # region code settings verification  --------------
                    if len(code) == 0 and settingsMode == True and readyToConfig == False:
                        printHeaderSettings()
                        code = code + MATRIX[row][col]
                        oled1.text("Pwd: " + code, 1, 22)
                        oled1.show()
                        break
                    elif len(code) == 0 and settingsMode == True and readyToConfig == True:
                        printHeaderSettings()
                        code = code + MATRIX[row][col]
                        oled1.text("Code: " + code, 1, 22)
                        oled1.show()
                        break
                    elif len(code) == 0 and settingsMode == False:
                        code = code + MATRIX[row][col]
                        oled1.text("Codigo: " + code, 1, 22)
                        oled1.show()
                        break
                    elif code[0:1] == '#' and settingsMode == False:
                        if code[1:] == _settingsCode:
                            settingsMode = True
                            song('ok')
                            printHeaderSettings()
                            cmdLineTitle = "Pwd:                  "
                            oled1.text(cmdLineTitle, 1, 22)
                            oled1.show()
                            settingsCode = ''
                            code = ''
                            break
                    elif code[0:1] == '#' and settingsMode == True and readyToConfig == False:
                        if code[1:] == pwdRST :
                            readyToConfig = True
                            oled1.fill(0)
                            printHeaderSettings()
                            oled1.text("Pwd: OK         ", 1, 22)
                            oled1.show()
                            song('ok')
                            utime.sleep(3)
                            printHeaderSettings()
                            oled1.text("Code:           ", 1, 22)
                            oled1.show()
                            if debugging:
                                # DisplayMsg('pwd ok',5)
                                print('pwd ok')
                            code = ''
                            settingsCode = ''
                            break
                        else:
                            oled1.fill(0)
                            printHeaderSettings()
                            oled1.text("Pwd: Error         ", 1, 22)
                            oled1.show()
                            song('fail')
                            utime.sleep(3)
                            printHeaderSettings()
                            oled1.text("Pwd:         ", 1, 22)
                            oled1.show()
                            if debugging:
                                # disable because not working ok
                                # DisplayMsg('pwd error', 5)
                                print('pwd error')
                            code = ''
                            break
                    elif code[0:1] != '#' and settingsMode == True and readyToConfig == True:
                        if changeSetting(code):
                            oled1.fill(0)
                            oled1.text('Applying', 1, 10)
                            oled1.text('code ' + code, 3, 22)
                            oled1.show()
                            utime.sleep(4)
                            song('ok')
                            oled1.fill(0)
                            printHeaderSettings()
                            oled1.text('Code:   ', 1, 22)
                            oled1.show()
                            code = ''
                        else:
                            oled1.fill(0)
                            oled1.text('Not Applied ', 1, 10)
                            oled1.text('code ' + code, 3, 22)
                            oled1.show()
                            utime.sleep(4)
                            song('fail')
                            oled1.fill(0)
                            printHeaderSettings()
                            oled1.text('Code:   ', 1, 22)
                            oled1.show()
                            code = ''

                        break
                    elif code[0:1] == '#' and code[1:] == _settingsCode and settingsMode == True and readyToConfig == True:
                        oled1.fill(0)
                        printHeaderSettings()
                        oled1.text("exit settings", 1, 22)
                        oled1.show()
                        song('ok')
                        utime.sleep(3)
                        printHeader()
                        oled1.text("Codigo:           ", 1, 22)
                        oled1.show()
                        code = ''
                        settingsCode = ''
                        readyToConfig = False
                        settingsMode = False
                        break
                    elif len(code) > 0 and settingsMode == True and readyToConfig == False:
                        if code == pwdRST:
                            readyToConfig = True
                            oled1.fill(0)
                            printHeaderSettings()
                            oled1.text("Pwd: OK         ", 1, 22)
                            oled1.show()
                            song('ok')
                            utime.sleep(3)
                            printHeaderSettings()
                            oled1.text("Code:           ", 1, 22)
                            oled1.show()
                            if debugging:
                                # disable because not working ok
                                # DisplayMsg('pwd ok', 5)
                                print('pwd ok')
                            code = ''
                            settingsCode = ''
                            break
                        else:
                            oled1.fill(0)
                            printHeaderSettings()
                            oled1.text("Pwd: Error         ", 1, 22)
                            oled1.show()
                            song('fail')
                            utime.sleep(3)
                            printHeaderSettings()
                            oled1.text("Pwd:         ", 1, 22)
                            oled1.show()
                            if debugging:
                                # disable because not working ok
                                # DisplayMsg('pwd error',4)
                                print('pwd error')
                            code = ''
                            break
                    # endregion -------------------------------------
                    # 
                    elif len(code) > 5 and code[0:1] != '#':
                        my_timer = 0
                        cleanCodes(1, '')
                        verifyCode(code)
                        break
                    # Wrong code less than 6 len
                    elif len(code) > 0 and settingsMode == False and readyToConfig == False:
                        oled1.fill(0)
                        printHeader()
                        oled1.text('Incompleto', 5, 22)
                        oled1.show()
                        song('fail')
                        utime.sleep(3)
                        printHeader()
                        if show_code:
                            oled1.text("Codigo: " + code, 1, 22)
                        else:
                            oled1.text("Codigo: " + code_hide, 1, 22)
                        oled1.show()
                        warning_message_active = True
                        break
                    code = code_hide = ''
                else:
                    code = code + MATRIX[row][col]
                    code_hide = code_hide + code_hide_mark
                
                if settingsMode == True :
                    printHeaderSettings()
                    if readyToConfig == False:
                        oled1.text("Pwd: " + code, 1, 22)
                    else:
                        oled1.text("Code: " + code, 1, 22)
                else:
                    printHeader()
                    if show_code:
                        oled1.text("Codigo: " + code, 1, 22)
                    else:
                        oled1.text("Codigo: " + code_hide, 1, 22)
                    if (len(active_codes['codes']) > 0) and settingsCode == False:
                        oled1.text(str(len(active_codes['codes']))+'', 1, 9)
                oled1.show()
                last_key_press = MATRIX[row][col]

            else:  #Screen saver counter start -----------------------------------
                if screen_saver <= 2000:
                    screen_saver += 1
                    if screen_saver == 2000:# ------ Screen Off --------------
                        screenSaver()

def getLocalTimestamp():
    global timestamp
    tsf = ((str(timestamp[0:2]) + '-' + str(timestamp[3:5]) + '-' +
          str(timestamp[6:8]) + 'T' + str(timestamp[9:11]) + ':' +
          str(timestamp[12:14]) + ':' + str(timestamp[15:17])))
    return tsf


'''
#----------------------------------------------
# msg: message to send
# type: to send Normal or write to memory to send later
#      n: Normal, w: Write to memory
# time: time to wait for assign message 
#---------------------------------------------
'''

def sendSMS(msg, type = 'n', time = 1, trigger = 0):
    global admin_sim
    for i, item in enumerate(admin_sim):
        if debugging:
            print('sent msg to: ' + item)
        utime.sleep(1)
        if type == 'n':
            # gsm.write('AT+CMGS="' + item + '"\r\n')
            # utime.sleep(time)
            # gsm.write(str(msg) + "\r\n")
            # gsm.write('\x1A')  # Enable to send SMS
            # utime.sleep(1)


            gsm.write('AT+CMGS="' + item + '"\r')
            utime.sleep(time)
            gsm.write(str(msg) + "\r\x1A")  # '\x1A' Enable to send SMS
            # gsm.write('\x1A')  # Enable to send SMS
            utime.sleep(1)

        else: # write to memory
            gsm.write('AT+CMGW="' + item +  '"\r')
            utime.sleep(time)
            gsm.write(str(msg) + "\r\x1A")
            utime.sleep(time)
            # if trigger == 1:
            #     utime.sleep(time)
            #     gsm.write('AT+CMSS=3"' + item + '"\r')
            #     utime.sleep(time)


def simResponse(timer):
    # def simResponse():
    global tupleToday
    global Today
    global gsm_status
    global sendStatus  # used to collect more information from sim800L
                       # like CBC, CSQ values
    global openByCode
    global MATRIX
    global cmdLineTitle
    global debugging
    global settingsCode
    global _settingsCode
    global pwdRST
    global demo
    global oled1
    global i2c1
    global rotate_display
    global sendCodeEvents
    global coreId

    msg = ''
    # try:

    if gsm.any() > 0:
        response = str(gsm.readline(), encoding).rstrip('\r\n') # type: ignore
        header = response.split(',')
        
        utime.sleep(0.5)
        if debugging:
            print(response)
            # tools.append_line_to_file('log.txt', 'response: ' + response + "      " + getLocalTimestamp())
            
        if 'ERROR' in response:
            print('simResponse,Error detected: ' + response)

        # elif 'DOWNLOAD' in response:  # sending email
        #     utime.sleep(1)
        #     print('at download..')
        #     gsm.write('"Hello"\r')
        #     utime.sleep(4)

        elif '+CREG:' in response:  # Get sim card status
            global simStatus
            # response = str(gsm.readline(), encoding).rstrip('\r\n')
            pos = response.index(':')
            simStatus = response[pos + 4: len(response)]
            if debugging:
                print('sim status --> ' + simStatus)
            return simStatus
        elif '+CCLK' in response:  # Get timestamp from GSM network
            global timestamp
            response = str(gsm.readline(), encoding).rstrip('\r\n') # type: ignore
            if debugging:
                print('sim status: ' + response)
            pos = response.index(':')
            timestamp = response[pos + 3: len(response) - 1]
            if debugging:
                print('GSM timestamp --> ' + timestamp)
                print(('Params --> ' ,timestamp[0:2],timestamp[3:5],
                       timestamp[6:8],timestamp[9:11],timestamp[12:14],
                       timestamp[15:17]))

                print('rtc_datetime --> ' + str(rtc.datetime()))

            rtc.datetime((int('20' + timestamp[0:2]), int(timestamp[3:5]),
                          int(timestamp[6:8]), 0, int(timestamp[9:11]),
                          int(timestamp[12:14]), int(timestamp[15:17]), 0))
            timestamplocal = timestamp.split(',')[0].split('/')
            tupleToday = (int(timestamplocal[0]), int(timestamplocal[1]), int(timestamplocal[2]))
            Today = timestamplocal[0] + '.' + timestamplocal[1] + '.' + timestamplocal[2]

        # SMS----------------------
        elif '+CMT:' in response:
            senderSim = header[0][header[0].index('"') + 1: -1]

            utime.sleep(0.5)
            if debugging:
                print('senderSim: ', senderSim)
                # tools.append_line_to_file('log.txt', 'senderSim: ' + senderSim + "      " + getLocalTimestamp())
            if(len(senderSim) >= 10):
                senderSim = senderSim[-10:]

            # Line to get SMS text
            response = str(gsm.readline(), encoding).rstrip('\r\n')

            role = jsonTools.updJson('r', 'restraint.json','user', 'sim', senderSim, True,'role')
            

            # Check extrange sender----------------------------------
            if not jsonTools.updJson('r', 'restraint.json','user', 'sim', senderSim, False):
                timestamp = getLocalTimestamp()
                pkg = { "sim" : senderSim, "cmd" : response, "eventAt" : timestamp }
                jsonTools.updJson('c', 'extrange.json','events', '', pkg)

                #  --- send extrage info to admin  -------
                sendSMS('Extrange sim: ' + senderSim + ' \n,cmd: ' + response
                         + '\n, at: ' + timestamp )
                
                utime.sleep(0.5)
                if debugging:
                    print('Extrange attempted')
                    # tools.append_line_to_file('log.txt', 'Extrange attempted: ' + senderSim + "      " + getLocalTimestamp())
                    showMsg('Extrange attempted')
                return
            
            # Check if user is lock  -------------------------------------
            # status = jsonTools.updJson('r', 'restraint.json','sim', senderSim,'',True,'status')
            # if status == 'lock' or status != 'unlock':

            utime.sleep(0.5)
            if isLocked(senderSim):
                if debugging:
                    print('User locked')
                    # tools.append_line_to_file('log.txt', 'User locked: ' + senderSim + "      " + getLocalTimestamp())
                    showMsg('User locked')
                return

            if 'twilio' in response.lower():
                msg = response.split("-")
                lenght = len(response)
                index = response.find('-')
                msg = response[index + 2:lenght].split(',')
            else:
                msg = response.split(",")

            utime.sleep(0.5)
            if debugging:
                print('GSM response: ' + response)
                # tools.append_line_to_file('log.txt', 'GSM response: ' + response + "      " + getLocalTimestamp())
                print('sender Sim --> ',senderSim)

            if (correctTime(msg[1])):
                # receiving codes ------------------
                if msg[0].strip() == 'codigo':
                    if len(msg) > 5:
                        msg[4] = msg[4].rstrip('\r\n')
                        msg[5] = msg[5].rstrip('\r\n')
                        api_data = {"userId": msg[4], "date": msg[3],
                                    "code": msg[2], "visitorSim": msg[5],
                                    "codeId": msg[6]}
                        jsonTools.updJson('c', 'codes.json','codes', '', api_data)
                        cleanCodes(1, '')
                        ShowMainFrame()
                        return
                
                elif msg[0].strip() == 'open':
                    # wait time to secure open each event, because before only open each second open sms
                    utime.sleep(0.5)

                    if debugging:
                        print('Abriendo ', msg)
                
                    if 'peatonal' in msg[2]:
                        magnet.Activate()
                        
                    elif 'vehicular' in msg[2]:
                        gate.Activate()

                    reg_local_event({'door':msg[2],'phone': senderSim,'phoneId': msg[3], 'date': toHumanDate(1,utime.gmtime(int(msg[1][:10])))})
                    return
                   
                
            # region admin or neighborAdmin commands section -------------------------------------
                
                if isAnyAdmin(senderSim):
                    if msg[0].strip() == 'newUser':
                        if not jsonTools.updJson('r', 'restraint.json','user', 'sim', msg[4], False):
                            api_data = { "name": msg[2], "house": msg[3], "sim": msg[4],
                                            "status": "unlock","id": msg[5],"role": msg[6],
                                            "lockedAt": getLocalTimestamp()}
                            jsonTools.updJson('c', 'restraint.json','user', '',api_data, '')
                        else:
                            if(debugging):
                                print('Ya existe usuario')
                                showMsg('Ya existe usuario')

                        return
                    
                    elif msg[0].strip() == 'updSim':
                        jsonTools.updJson('updSim', 'restraint.json','user','sim', msg[2],
                                        False, msg[3], getLocalTimestamp())
                        return

                    elif msg[0].strip() == 'updStatus_lock' or msg[0].strip() == 'updStatus_unlock':
                        jsonTools.updJson(msg[0].strip(), 'restraint.json','user','sim', msg[4],
                                        False,'',getLocalTimestamp())
                        updRestraintList()
                        return
                    
                    elif msg[0].strip() == 'delete':
                        jsonTools.updJson('d','restraint.json','user','id',msg[2],
                                        False,'',getLocalTimestamp())
                        updRestraintList()
                        return
                    
                    elif msg[0] == 'active_codes':
                        sendSMS('codes available: ' + pkgListCodes())
                        return
                    elif msg[0] == 'diskStatus':
                        sendSMS(diskUsage(True))
                        return
                    
                    elif msg[0] == 'memStatus':
                        sendSMS(memUsage(True))
                        return
                    
                else:
                    if debugging:
                        print('no privileges', msg)
                    return
                
                    
            #endregion admin  -------------------------------------------------

            #region super admin ------------------------------------------
                if isAdmin(senderSim):
                    if msg[0] == 'status':
                        if msg[2] == 'gral':
                            sendStatus = True
                            signal_Status('Status')

                        elif msg[2] == 'restraint':
                            txtJson('restraint.json','user')
                        elif msg[2] == 'getConfig':
                            gsm_status = []
                            gsm_status.append({jsonTools.showData('config.json','app','coreId')})
                            gsm_status.append({jsonTools.showData('config.json','app','admin_sim')})
                            gsm_status.append({jsonTools.showData('config.json','app','demo')})
                            gsm_status.append({jsonTools.showData('config.json','app','openByCode')})
                            gsm_status.append({jsonTools.showData('config.json','app','settingsCode')})
                            gsm_status.append({jsonTools.showData('config.json','app','pwdRST')})
                            gsm_status.append({jsonTools.showData('config.json','sim','value')})
                            gsm_status.append({jsonTools.showData('config.json','sim','url')})
                            gsm_status.append({jsonTools.showData('config.json','sim','api_codes_events')})
                            gsm_status.append({jsonTools.showData('config.json','sim','sendCodeEvents')})
                            sendSMS(str(gsm_status))
                        elif msg[2] == 'extrange':
                            txtJson('extrange.json','events')
                        return
                    elif msg[0] == 'query':
                        sendSMS(jsonTools.showData(msg[2], msg[3], msg[4]))
                        return
                    elif msg[0] == 'uploadEvents':
                        uploadCurrentStatus('events')
                        return
                    
                    elif msg[0] == 'uploadRestraint':
                        uploadCurrentStatus('restraint')
                        return
                    
                    elif msg[0] == 'uploadCodes':
                        uploadCurrentStatus('codes')
                        return
                    
                    elif msg[0] == 'uploadExtrange':
                        uploadCurrentStatus('extrange')
                        return
                    
                    elif msg[0] == 'blockExtrange':
                        if not jsonTools.updJson('r', 'restraint.json','user', 'sim', msg[3], False):
                            api_data = { "name": msg[2], "house": "NA", "sim": msg[3],
                                            "status": "lock","id": msg[4],"role": 'extrange',
                                            "lockedAt": getLocalTimestamp()}
                            jsonTools.updJson('c', 'restraint.json','user', '',api_data, '')
                        else:
                            if(debugging):
                                print('Ya existe extrange')
                                showMsg('Ya existe extrange')

                        return
                    elif msg[0] == 'rst':
                        softReset()
                        return

                    elif msg[0] == 'cfgCHG':
                        oled1.fill(0)
                        oled1.text(msg[3] + ' =', 2, 1)
                        oled1.text(msg[4], 2, 14)
                        oled1.show()
                        utime.sleep(4)
                        
                        if(msg[4] == 'false' or msg[4] == 'true'):
                            msg[4] = str_to_bool(msg[4])
                                    
                        jsonTools.updJson('u','config.json',msg[2], msg[3], msg[4])
                            
                        if msg[3] == 'openByCode':
                            openByCode = msg[3]

                        if msg[3] == 'demo':
                            demo = msg[4]

                        if msg[3] == 'rotate':
                            rotate_display = msg[4]
                            i2c1 = I2C(1, scl=Pin(scl1), sda=Pin(sda1), freq=400000)
                            oled1 = SSD1306_I2C(WIDTH, HEIGHT, i2c1)
                            oled1.rotate(3)
                        
                        if msg[3] == 'debugging':
                            debugging = msg[4]
                            if debugging:
                                tim25.init(freq=2, mode=Timer.PERIODIC, callback=tick25)
                            else:
                                tim25.deinit()

                        if msg[2] == 'keypad_matrix':
                                MATRIX = config[msg[2]][msg[4]]

                        if msg[3] == 'settingsCode':
                            _settingsCode = msg[4]
                        
                        if msg[3] == 'pwdRST':
                            pwdRST = msg[4]

                        if msg[3] == 'sendCodeEvents':
                            sendCodeEvents = msg[4]

                        if msg[3] == 'coreId':
                            coreId = msg[4]

                        ShowMainFrame()
                        return    
            #endregion super admin--------------------
            else:
                if debugging:
                    print('out of time')
                    showMsg('out of time')

        elif '+CSQ:' in response:
            
            pos = response.index(':')
            print('entre aqui response: ', response)

            # global response_return
            response_return = response[pos + 2: (pos + 2) + 2]
            if sendStatus:
                gsm_status.append({'CSQ': response_return})
            elif debugging:
                print('CSQ : ', response_return)

            # return (response_return)
        elif '+CBC:' in response:
            pos = response.index(':')
            response_return = response[pos + 2: (pos + 2) + 9]
            d = RTC()
 
            if sendStatus:
                sendStatus = False
                gsm_status.append({'coreId': coreId})
                gsm_status.append({'Local': toHumanDate(2,d.datetime())})
                gsm_status.append({'CBC': response_return})
                pcbTemp = getBoardTemp()
                gsm_status.append({'Temp': pcbTemp})
                # gsm_status.append({'RTC': d.datetime()})

                #  --- send status  -------
                sendSMS(str(gsm_status) + '\n Codes: ' + pkgListCodes()
                        + '\n locked: ' + pkgListAccess())

            if debugging:
                print('CBC : ', response_return)
        # return (response_return)
        elif '+CGREG:' in response:
            pos = response.index(':')
            response_return = response[pos + 4: (pos + 4) + 1]
            cgreg_status = response_return
        elif '+CNUM:' in response:
            if sendStatus:
                sendStatus = False
                sendSMS('Phone Num: ' + response)
        elif 'OVER-VOLTAGE' in response:  # 4.27v
            sendStatus = True
            showMsg('Temp high')
            if debugging:
                print('GSM Module Temperature high !')
            gsm.write('AT+CBC\r')
        elif 'UNDER-VOLTAGE' in response:  # 3.48v
            sendStatus = True
            showMsg('Temp low')
            if debugging:
                print('GSM Module Temperature low')
            gsm.write('AT+CBC\r')
    # except NameError:
    #     print('Error -->', NameError)
    #     pass
    if not debugging: 
        led25.value(0)


def tagResponse(timer):
    global lastTag
    if nfc.any():
        try:
            ID = ''
            readByte = nfc.read()
            pass
            decoded = int(readByte[3:11].decode('utf-8'),16)
            if lastTag != decoded:
                lastTag = decoded
                print('Tad Id: ', decoded)
            

        except ValueError as identifier:
            print('Can not read: ', identifier)
# endregion ------ Timers  -----------------------------------


def displayErrors():
    oled1.fill(0)
    oled1.text("Bytheg", 20, 0)
    oled1.text("Exc: " + Exceptions, 2, 15)
    oled1.show()


def getBoardTemp():
    sensor_temp = ADC(4)
    conversion_factor = 3.3 / (65535)
    reading = sensor_temp.read_u16() * conversion_factor
    mc_temp = 27 - (reading - 0.706) / 0.001721
    return str(round(mc_temp, 1))


def pkgListCodes():
    global codes
    global active_codes
    codes = ''
    for i, item in enumerate(active_codes['codes']):
        codes = codes + item['code'] + ','
    return codes

def pkgListAccess():
    global access
    access = ''
    for i, item in enumerate(restraint_list['user']):
        if item['status'] == 'lock':
            print('pkgListCodes lock: ' + item['name'])
            access = access + item['name'] + '-[' + item['house'] + '],'
    return access

def isLocked(sim):
    locked = True
    for i, item in enumerate(restraint_list['user']):
        if len(item['sim']) == len(sim):
            if item['sim'] == sim:
                if item['status'] == 'unlock':
                    locked = False
                    break
        else:
            if len(item['sim']) < len(sim):
                if item['sim'] in sim:
                    if item['status'] == 'unlock':
                        locked = False
                        break
            else:
                if sim in item['sim']:
                    if item['status'] == 'unlock':
                        locked = False
                        break
    return locked

def isAnyAdmin(sim):
    admin = False
    for i, item in enumerate(restraint_list['user']):
        if len(item['sim']) == len(sim):
            if item['sim'] == sim:
                if item['role'] in ['admin','neighborAdmin']:
                    admin = True
                    break
        else:
            if len(item['sim']) < len(sim):
                if item['sim'] in sim:
                    if item['role'] in ['admin','neighborAdmin']:
                        admin = True
                        break
            else:
                if sim in item['sim']:
                    if item['role'] in ['admin','neighborAdmin']:
                        admin = True
                        break    
    return admin


def isAdmin(sim):
    admin = False
    for i, item in enumerate(restraint_list['user']):
        if len(item['sim']) == len(sim):
            if item['sim'] == sim:
                if item['role'] == 'admin':
                    admin = True
                    break
        else:
            if len(item['sim']) < len(sim):
                if item['sim'] in sim:
                    if item['role'] == 'admin':
                        admin = True
            else:
                if sim in item['sim']:
                    if item['role'] == 'admin':
                        admin = True
    if debugging:
        if admin:
            print('Yes, it is Admin')
        else:
            print('It is Not Admin')

    return admin

# --- Verify if sim card is inserted ---
def simInserted():
    gsm.write('AT+CREG?\r')
    utime.sleep(0.7)

def sendJson(file):
    jsonObj = open(file, "r")
    file_list = json.loads(jsonObj.read())

    jsonObj.close()

def updRestraintList():
    global restraint_list
    jaccess = open('restraint.json')
    restraint_list = json.loads(jaccess.read())
    jaccess.close()

'''
#---------------------------------------------
# file: json file name to read
# key:  key to read
# Desc: Convert Json file to text 
#--------------------------------------------
'''
def txtJson(file, key):
    jsonObj = open(file, "r")
    json_list = json.loads(jsonObj.read())
    jsonObj.close()
   
    arr = []
    for i, item in enumerate(json_list[key]):
        arr.append({item['name'],item['house'],item['status']})
        # arr.append(item)

    if(len(arr) == 0):
        arr.append(file + ' empty')
    else:
        # sorting
        # for i,iitem in enumerate(arr):
        #     for j,jitem in enumerate(arr):
        #         if len(arr) > j + 1 :
        #             if arr[j]['house'] > arr[j + 1]['house']:
        #                 temp = arr[j]
        #                 arr[j] = arr[j + 1]
        #                 arr[j + 1] = temp

        arr_send = []
        pkg_size = 0
        total_size = 0
        for i,iitem in enumerate(arr):
            arr_send.append(iitem)
            pkg_size += len(str(iitem))

            if (1024 - pkg_size) <= 52:
                print('middle pkg size: ' + str(pkg_size))
                print('send middle pkg: ', arr_send)
                print('\n')
                total_size += pkg_size
                sendSMS(arr_send, 'n')
                utime.sleep(10)
                pkg_size = 0
                arr_send.clear()
      

        if len(str(arr_send)) > 0 :
            total_size += pkg_size
            print('\n')
            print('last pkg size: ' + str(pkg_size))
            print('last pkg to send: ',arr_send)
            print('final size: ' + str(total_size))
            sendSMS(arr_send, 'n')
            utime.sleep(10)


def sendCommand(command):
    smd= command
    smd=smd+'\r\n'
    smds=smd.encode('ascii')
    gsm.write(smds)
    utime.sleep(1)
    # line = gsm.read(80).decode('ascii').rstrip()
    # print(line)
   
def sendEmail():
    # EMAIL  - - - - -
    USERNAME = "ricardogueta@gmail.com"  # Username for authentication
    PASSWORD = "qyrhfseormkjjqug"  # Password for authentication
    # PASSWORD = "qyrhfseormkjjqug"  # Password for authentication
    SMTP_SERVER = "smtp.gmail.com"  # URL of SMTP server
    # SSL_PORT = 465 #message sumbmission over SSL protocal
    SSL_PORT = 587 #message sumbmission over TLS protocal

    FROM = "ricardogueta@gmail.com"  # Name shown as sender
    TO = "ricardogueta@gmail.com" # Mail address of the recipient
    NAME = "privada_San_Juan"
    message = "hello"

    gsm.write('AT+CMEE=2\r') # Enable result code and use verbose values (will expand upon errors)
    utime.sleep(2)

    # gsm.write('AT+EMAILSSL=1\r') # 
    # utime.sleep(2)

    gsm.write('AT+EMAILCID=1\r') # Set paramaters of Email
    utime.sleep(2)

    # gsm.write('AT+EMAILTO=30\r') # Timeout for server response (defult 30 secs)
    # utime.sleep(2)

    gsm.write('AT+SMTPSRV="{}",{}\r'.format(SMTP_SERVER, SSL_PORT)) # Set SMTP server address and port
    utime.sleep(2)

    gsm.write('AT+SMTPAUTH=1,"{}","{}"\r'.format(USERNAME,PASSWORD)) # Set username and password.
    utime.sleep(4)

    gsm.write('AT+SMTPFROM="{}","{}"\r'.format(USERNAME,FROM)) # Set sender address and name
    utime.sleep(2)

    gsm.write('AT+SMTPRCPT=0,0,"{}","{}"\r'.format(TO,NAME)) # Set the recipients name
    utime.sleep(2)

    # gsm.write('AT+SMTPSUB="{}"\r'.format("This is sent from the core San Juan")) # Body of text
    gsm.write('AT+SMTPSUB="Test"\r') # Body of text
    utime.sleep(1)

    lengthOfMessage = len(message)
    gsm.write('AT+SMTPBODY={}\r'.format(str(lengthOfMessage))) #shouldn't be quoted
    utime.sleep(3)

    # gsm.write('{}\r'.format(message))
    # utime.sleep(3.5)

    gsm.write('AT+SMTPSEND\r')
    utime.sleep(10)


# endregion ------  functions --------------------------------------------------

    
try:
    # region  ----------------    Open CODES JSON files  --------------------

    code = ''
    code_hide = ''

    try:
        jcodes = open('codes.json')
        code_list = json.loads(jcodes.read())
        jcodes.close()

    except OSError:  # Open failed
        print('Error--> ', OSError)

    try:
        updRestraintList()

    except OSError:  # Open failed
        print('Error--> ', OSError)


    # endregion  -----------------------------


    # ---  Check  GSM module sim ------
    if simInserted() == "0":
        if debugging:
            print('Modulo GSM no tiene sim')
        oled1.fill(0)
        oled1.text("No SIM", 10, 15)
        oled1.show()
    else:
        led25 = Pin(25, Pin.OUT)
        led25.value(0)

        # Initialize timer led blink
        tim25 = Timer()

        # Initialize and set all the rows to low
        InitKeypad()
        #-------  SETUP GSM device  -------------------
        init_gsm()

        # Initialize timer Used for polling keypad
        timerKeypad = Timer()

        # Initialize timer used for sim800L
        timerSim800L = Timer()

        # Initialize timer used RDM6300
        timerRDM6300= Timer()

        # Activate blink led
        if debugging:
            tim25.init(freq=2, mode=Timer.PERIODIC, callback=tick25)

        timerSim800L.init(freq=2, mode=Timer.PERIODIC, callback=simResponse)

        timerKeypad.init(freq=2, mode=Timer.PERIODIC, callback=PollKeypad)

        timerRDM6300.init(freq=2, mode=Timer.PERIODIC, callback=tagResponse)

        # ------ Timestamp section   ---------------------
        rtc = RTC()
        rtc_date = RTC().datetime()

        initial()
        song('initial')

    diskUsage()
    memUsage()

    # send email
        # if debugging:
        #     print('sending email')
        # utime.sleep(2)
        # sendEmail()
    
except OSError:  # Open failed
    print('Error--> ', OSError)
except SystemExit as e:
    import os
    print('Error SystemExit --> ', e)
    os._exit()
