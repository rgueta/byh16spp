import machine
from machine import UART, Pin, I2C, Timer, RTC, ADC, PWM
import os
import uasyncio
import _thread
from ssd1306_non_rotate import SSD1306_I2C
import json
import utime
import magnet
import gate
import initSetup
# import time

# region --------  Setup config json file  ------------------

conf = open('config.json')
config = json.loads(conf.read())
conf.close()
# endregion ----------------

# region --------  Setup Events json file  ------------------

event = open('events.json')
events_log = json.loads(event.read())
event.close()
# endregion ----------------

# region ------     Variables     ------------------
# wait until gsm device connect to network

utime.sleep(14)
# -------------------------------------

debugging = config['app']['debugging']
Exceptions = ''
timestamp = ''
tupleToday = ()
emptyTuple = ()
Today = ''
gsm_status = []
sendStatus = False
active_codes = {"codes": []}
show_code = config['app']['show_code']
buzzer_pin = config['pi_pins']['buzzer']

# ----- Intialization -----------
buzzer = PWM(Pin(buzzer_pin))
if debugging:
    print('Version ..')
initSetup.Initial()

# ------------------ Setup GSM -----------------------
gsm_tx = config['pi_pins']['gsm_TX']
gsm_rx = config['pi_pins']['gsm_RX']
encoding = 'utf-8'
# gsm = UART(0, 9600, tx=Pin(gsm_tx), rx=Pin(gsm_rx), rxbuf=512)
gsm = UART(0, 9600, tx=Pin(gsm_tx), rx=Pin(gsm_rx))

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

# i2c = I2C(0)
i2c1 = I2C(1, scl=Pin(scl1), sda=Pin(sda1), freq=400000)
# i2c2 = I2C(0, scl=Pin(scl2), sda=Pin(sda2), freq=400000)

oled1 = SSD1306_I2C(WIDTH, HEIGHT, i2c1)
oled1.rotate(2)
# oled2 = SSD1306_I2C(WIDTH, HEIGHT, i2c2)

# endregion -------------------------------------------------------

# region ------------- Key pad gpio setup  ----------------------------
KEY_UP = const(0)
KEY_DOWN = const(1)

MATRIX = config['keypad_matrix']
ROWS = config['pi_pins']['keypad_rows']
COLS = config['pi_pins']['keypad_cols']

row_pins = [Pin(pin_name, mode=Pin.OUT) for pin_name in ROWS]
col_pins = [Pin(pin_name, pull=Pin.PULL_DOWN) for pin_name in COLS]

# endregion -----------------------------------------

# region ------------ SIM800L  -----------------------

send_code_events = config['sim']['send_code_events']
admin_sim = config['app']['admin_sim'].split(',')

app_version = config['app']['app_version']
apn = config['sim']['apn']
url = config['sim']['url'] + config['sim']['api_elerts'] + config['app']['pedestrian_alert_msg'] + '/' + config['sim'][
    'value']
serial_port = config['sim']['serial_port']
serial_baud = config['sim']['serial_baud']
serial_timeout = config['sim']['serial_timeout']
HTTPACTION_waitTime = config['sim']['HTTPACTION_waitTime']
api_get_line = config['sim']['api_get_line']

APN_USER = 'AT+SAPBR=3,1,"USER","%s"\r' % config['sim']['APN_USER']
APN_PWD = 'AT+SAPBR=3,1,"PWD","%s"\r' % config['sim']['APN_PWD']
incoming_calls = config['sim']['incoming_calls']

# initial gprs configuration
def gsm_config_gprs():
    print(" --- CONFIG GPRS --- ");
    gsm.write('AT+SAPBR=3,1,"Contype","GPRS"\r\n')
    utime.sleep(1)

    # global keepMonitorSIM800L
    instr = 'AT+SAPBR=3,1,"APN","%s"\r\n' % apn
    gsm.write(instr.encode())
    utime.sleep(1)




# endregion  -------------------------------------


# endregion  -----------------  Variable  ---------------------------

# region----- Functions --------------------

def initial():
    gsm.write('AT+CCLK?\r')
    # cleanup expired codes
    utime.sleep(5)

    # if tupleToday == emptyTuple:
    #     print('tupleToday esta VACIO', tupleToday)
    #     Exceptions = Exceptions + '1,'
    #     displayErrors()
    # #     cleanCodes(1,'')
    # else:
    #     cleanCodes(1, '')

    cleanCodes(1, '')

    oled1.fill(0)
    oled1.text("* <-", 1, 0)
    oled1.text(Today[-2:], 45, 0)
    oled1.text('# enter', 75, 0)
    if len(active_codes) > 0:
        oled1.text("..", 1, 9)
    #     oled1.text(Today,64,0)
    oled1.text("Codigo: ", 1, 22)
    oled1.show()

    gsm_config_gprs()


def init_gsm():
    # gsm.write('ATE0\r')    # Disable the Echo
    # utime.sleep(0.5)
    gsm.write('AT+CMGF=1\r')  # Select Message format as Text mode
    utime.sleep(0.6)
    # print(gsm.read().decode())
    # sim800()
    gsm.write('AT+CNMI=1,2,0,0,0\r')  # New SMS Message Indications
    utime.sleep(0.6)

    # gsm.write('AT+CGATT?\r\n')
    # utime.sleep(1)

    if(not incoming_calls):
        gsm.write('AT+GSMBUSY=1\r')
        utime.sleep(0.6)

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


def unblockUser(uuid):
    jaccess = open("restraint.json", "r")
    restraint_list = json.loads(jaccess.read())
    jaccess.close()

    for i, item in enumerate(restraint_list['user']):
        if item['uuid'] == uuid:
            del restraint_list['user'][i]
            print('Dar acceso a este usuario ' + item['name'])
            f = open("restraint.json","w")
            json.dump(restraint_list, f)
            f.close()
            break

def verifyRestraint(uuid):
    exists = False
    jaccess = open('restraint.json')
    restraint_list = json.loads(jaccess.read())
    jaccess.close()
    for i, item in enumerate(restraint_list['user']):
        if item['uuid'] == uuid:
            print('Ya existe este usuario')
            exists = True
            break
    return exists

def insertJson(pkg, file):
    global jcodes
    global code_list
    global restraint_list
    try:  # if os.path.exists(file):
        with open(file, 'r+', encoding='utf8') as jsonFile:
            #     # First we load existing data into a dict.
            file_data = json.load(jsonFile)
            if file == 'codes.json':
                file_data['codes'].append(pkg)
            elif file == 'restraint.json':
                file_data['user'].append(pkg)
            elif file == 'events.json':
                file_data['events'].append(pkg)
        f = open(file, "w")
        json.dump(file_data, f)
        f.close()
        if file == 'codes.json':
            jcodes = open('codes.json')
            code_list = json.loads(jcodes.read())
            jcodes.close()
        elif file == 'restraint.json':
            jfiles = open('restraint.json')
            restraint_list = json.loads(jfiles.read())
            jfiles.close()

    except FileNotFoundError as exc:  # create file not exists
        print('InsertJson Error --> ', FileNotFoundError)
        pass

def tupleDateFROM_ISO(d):  # get just date from ISO datetime format '2022-01-05T10:53:13.00'
    tPosition = d.index('T')
    onlyDate = d[0:tPosition].split('-')
    tupleDate = (int(onlyDate[0][2:]), int(onlyDate[1]), int(onlyDate[2]))
    return tupleDate


def daysBetween(d1, d2):
    d1 += (1, 0, 0, 0, 0)  # ensure a time past midnight
    d2 += (1, 0, 0, 0, 0)
    return utime.mktime(d1) // (24 * 3600) - utime.mktime(d2) // (24 * 3600)


# region -----------  codes  --------------------
# ---  1 : by date, 2 : by duplicity
def cleanCodes(type, code):
    global active_codes
    active_codes = {"codes": []}

    now = utime.time()  # create timestamp from rtc local
    jcodes = open('codes.json')
    code_list = json.loads(jcodes.read())
    jcodes.close()

    for i, item in enumerate(code_list['codes']):
        if type == 1:
            dtcode = utime.mktime((2000 + int(item['date'][2:4]), int(item['date'][5:7]),
                                  int(item['date'][8:10]), int(item['date'][11:13]),
                                  int(item['date'][14:16]), int(item['date'][17:19]),
                                  0,0))

            if dtcode < now :
            # instead of days_between check it out
            # days_between = daysBetween(tupleDateFROM_ISO(item['date']), tupleToday)
            # print('code --> ' + item['code'] +
            #       ', date: ' + item['date'] + ', daysBetweeb --> ', days_between)
            # if days_between < 0:

                # del code_list['codes'][i]

                print('Code deleted --> ', item['code'])
            else:
                print('--- adding code to active_codes ------> ' + str(item['code']))
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


def verifyCode(code):
    global active_codes
    for i, item in enumerate(active_codes['codes']):
        if code == item['code']:
            print('codigo valido..! userId : ' + str(item['userId']))
            song('ok')
            magnet.Activate()
            if send_code_events:
                # reg_code_event(str(item['codeId']))
                # reg_code_event(code)
                reg_code_event_json(str(item['codeId']))
                print('Call API to store code event')
            else:
                event_pkg = {"codeId":str(item['codeId']),"picId":"NA",
                             "CoreSim":config['sim']['value'],"timestamp":
                             rtc.datetime()}

                insertJson(event_pkg,'events.json')
                # gsm.write('AT+CCLK?\r\n')
                utime.sleep(1)

                print('event registered locally')
            break

        elif i + 1 == len(active_codes):
            global warning_message_active
            print('codigo no valido..!')
            if show_code:
                oled1.text("Codigo: " + code, 1, 22)
            else:
                oled1.text("Codigo: " + code_hide, 1, 22)
            oled1.text("Codigo: " + code_hide, 1, 22)
            warning_message_active = True
            song('fail')


def reg_code_event(code_id):
    local_url = config['sim']['url'] + config['sim']['api_codes_events'] + code_id + '/NA/' + config['sim']['value']
    # local_url = config['sim']['url'] + config['sim']['api_codes_events']

    print('local_url --> ' + local_url)

    # gsm.write('AT+SAPBR=3,1,"Contype","GPRS"\r\n')
    # utime.sleep(1)

    # global keepMonitorSIM800L
    # instr = 'AT+SAPBR=3,1,"APN","%s"\r\n' % apn
    # gsm.write(instr.encode())
    # utime.sleep(1)

    # Enable bearer 1.
    gsm.write('AT+SAPBR=1,1\r\n')
    utime.sleep(3)

    gsm.write('AT+HTTPTERM\r\n')
    utime.sleep(1)

    gsm.write('AT+HTTPINIT\r\n')
    utime.sleep(1)

    gsm.write('AT+HTTPPARA="CID",1\r\n')
    utime.sleep(1)

    instr = 'AT+HTTPPARA="URL","%s"\r\n' % local_url
    gsm.write(instr.encode())
    utime.sleep(2)

    # gsm.write('AT+HTTPPARA="CONTENT","application/json"\r\n')
    # utime.sleep(1)

    gsm.write('AT+HTTPSSL=0\r\n')
    utime.sleep(0.5)

    # 0 = GET, 1 = POST, 2 = HEAD
    gsm.write('AT+HTTPACTION=1\r\n')
    utime.sleep(6)

    gsm.write('AT+HTTPREAD\r\n')
    utime.sleep(1)

    gsm.write('AT+HTTPTERM\r\n')
    utime.sleep(1)

    gsm.write('AT+SAPBR=0,1\r\n')
    utime.sleep(1)


def reg_code_event_json(code_id):
    Url = config['sim']['url'] + config['sim']['api_codes_events']
    print('Url --> ' + Url)

    pckgJson = {"codeId":code_id,"picId":"NA","CoreSim":config['sim']['value']}
    pckgJson_obj = json.dumps(pckgJson)
    pckgJson_size = len(pckgJson_obj)

    print('pckgJson -->', str(pckgJson))
    print('pckgJson_size --> ', pckgJson_size)

    # Enable bearer 1.
    gsm.write('AT+SAPBR=1,1\r\n')
    utime.sleep(3)

    # gsm.write('AT+SAPBR=2,1\r\n')
    # utime.sleep(2)

    # gsm.write('AT+HTTPTERM\r\n')
    # utime.sleep(1)

    gsm.write('AT+HTTPINIT\r\n')
    utime.sleep(2)

    gsm.write('AT+HTTPSSL=1\r\n')
    utime.sleep(2)

    gsm.write('AT+HTTPPARA="CID",1\r\n')
    utime.sleep(2)

    instr = 'AT+HTTPPARA="URL","%s"\r\n' % Url
    gsm.write(instr.encode())
    utime.sleep(2)

    # instr = 'AT+HTTPPARA="CONTENT","application/json"\r\n'
    gsm.write('AT+HTTPPARA="CONTENT","application/json"\r\n')
    # gsm.write(instr.encode())
    utime.sleep(2)

    gsm.write('AT+HTTPDATA=' + str(pckgJson_size) + ',5000\r\n')
    # gsm.write('AT+HTTPDATA=192,5000' + '\r\n')
    utime.sleep(4)

    gsm.write(json.dumps(pckgJson))
    utime.sleep(10)

    # 0 = GET, 1 = POST, 2 = HEAD
    gsm.write('AT+HTTPACTION=1\r\n')
    utime.sleep(3)

    gsm.write('AT+HTTPREAD\r\n')
    utime.sleep(3)
    #
    #
    gsm.write('AT+HTTPTERM\r\n')
    utime.sleep(3)
    #
    gsm.write('AT+SAPBR=0,1\r\n')
    utime.sleep(1)

def sendCodeToVisitor(code, visitorSim):
    #  --- send status  -------
    gsm.write('AT+CMGS="' + str(visitorSim, encoding) + '"\r')
    utime.sleep(0.5)
    gsm.write('Codigo de acceso: ' + code + "\r")
    utime.sleep(0.5)
    gsm.write(chr(26))
    utime.sleep(0.5)


# endregion --------  codes --------------------------------


# region ------ Timers  -----------------------------------
def tick25(timer):
    global led25
    led25.toggle()


def PollKeypad(timer):
    key = None
    global code
    global code_hide
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
                if MATRIX[row][col] == '*':
                    if (len(code) > 0):
                        code = code[0:-1]
                        code_hide = code_hide[0:-1]
                elif MATRIX[row][col] == '#':
                    if len(code) > 5:
                        my_timer = 0
                        cleanCodes(1, '')
                        verifyCode(code)
                    elif len(code) > 0:
                        oled1.fill(0)
                        #oled1.text("* Borrar      #Enter",1,0)
                        #oled1.text(Today,64,0)
                        printHeader()
                        oled1.text('Incompleto', 5, 22)
                        oled1.show()
                        song('fail')

                        utime.sleep(3)
                        #oled1.fill(0)
                        #oled1.text("* Borrar      #Enter",1,0)
                        printHeader()
                        #oled1.text(Today,64,0)
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
                oled1.fill(0)
                oled1.text("* <-", 1, 0)
                oled1.text(Today[-2:], 45, 0)
                oled1.text('# enter', 75, 0)
                #                     printHeader()
                #                 oled1.text(Today,64,0)
                if show_code:
                    oled1.text("Codigo: " + code, 1, 22)
                else:
                    oled1.text("Codigo: " + code_hide, 1, 22)
                if (len(active_codes) > 0):
                    oled1.text('..', 1, 9)
                oled1.show()
                last_key_press = MATRIX[row][col]
                print("Codigo:" + code)


def printHeader():
    oled1.fill(0)
    oled1.text("* <-", 1, 0)
    oled1.text(Today[-2:], 45, 0)
    oled1.text('# enter', 75, 0)
    if len(active_codes) > 0:
        oled1.text('..', 1, 9)


#   oled1.text(Today,64,0)

def getLocalTimestamp():
    ts = RTC().datetime()
    tsf = ((str(ts[0]) + '-' + str(ts[1]) + '-' +
            str(ts[2]) + 'T' + str(ts[4]) + ':' +
            str(ts[5]) + ':' + str(ts[6])))
    return tsf

def simResponse(timer):
    # def simResponse():
    global tupleToday
    global Today
    global gsm_status
    global sendStatus

    msg = ''
    # try:

    if gsm.any() > 0:
        #         response = gsm.read().decode().rstrip('\r\n')
        response = str(gsm.readline(), encoding).rstrip('\r\n')
        if debugging:
            print(response)
        if '+CREG:' in response:  # Get sim card status
            global simStatus
            # response = str(gsm.readline(), encoding).rstrip('\r\n')
            pos = response.index(':')
            simStatus = response[pos + 4: len(response)]
            return simStatus
            # if simStatus == "0":
            #     if debugging:
            #         print('Modulo GSM no tiene sim..!')
            #     oled1.fill(0)
            #     oled1.text("No SIM",10,15)
            #     oled1.show()
            #     sys.exit(0)

        elif '+CCLK' in response:  # Get timestamp from GSM network
            global timestamp
            response = str(gsm.readline(), encoding).rstrip('\r\n')
            pos = response.index(':')
            timestamp = response[pos + 3: len(response)]
            if debugging:
                print('GSM timestamp --> ' + timestamp)
                print(('Params --> ', timestamp[0:2],timestamp[3:5],
                       timestamp[6:8],timestamp[9:11],timestamp[12:14],
                       timestamp[15:17]))

                rtc.datetime((2000 + int(timestamp[0:2]), int(timestamp[3:5]),
                              int(timestamp[6:8]), 0,int(timestamp[9:11]),
                              int(timestamp[12:14]),int(timestamp[15:17]),0))

                # rtc_timestamp = rtc.datetime()
                print('rtc_datetime --> ' + str(rtc.datetime()))
                # print('GMS timestamp formated --> ' + rtc_timestamp)
                # t1 = datetime.strptime(timestamp_formated, "%y-%m-%dT%H:%M:%S")
                # print('T1 --> ', str(t1))

                timestamp = timestamp.split(',')[0].split('/')
                tupleToday = (int(timestamp[0]), int(timestamp[1]), int(timestamp[2]))
                Today = timestamp[0] + '.' + timestamp[1] + '.' + timestamp[2]
                print('GSM Net Timestamp: ', tupleToday)

        # SMS----------------------
        elif '+CMT:' in response:
            response = str(gsm.readline(), encoding).rstrip('\r\n')
            if 'twilio' in response.lower():
                msg = response.split("-")
                lenght = len(response)
                index = response.find('-')
                msg = response[index + 2:lenght].split(',')
            else:
                msg = response.split(",")
            if debugging:
                print('GSM Message: ', msg)
            # receiving codes ------------------
            if msg[0].strip() == 'codigo':
                msg[3] = msg[3].rstrip('\r\n')
                msg[4] = msg[4].rstrip('\r\n')
                api_data = {"userId": msg[3], "date": msg[2],
                            "code": msg[1], "visitorSim": msg[4],
                            "codeId": msg[5]}
                insertJson(api_data, 'codes.json')
                cleanCodes(1, '')

                # ----- Update available codes  -----
                #codesAvailable()
                #sendCodeToVisitor(msg[1],msg[4])

            elif msg[0].strip() == 'blocked':
                if not verifyRestraint(msg[4]):
                    api_data = { "name": msg[1], "email": msg[2], "uuid": msg[3],
                                "house": msg[4].rstrip('\r\n'),
                                "local": getLocalTimestamp()}
                    insertJson(api_data, 'restraint.json')
            elif msg[0].strip() == 'unblocked':
                api_data = {"name": msg[1], "email": msg[2], "uuid": msg[3],
                            "house": msg[4].rstrip('\r\n'),
                            "date": getLocalTimestamp()}
                unblockUser(msg[3])
                # ----- Update available codes  -----
                #   print('Es un acceso --> ' + str(datetime.now()) + ' - ' + response)
            elif msg[0].strip() == 'open':
                print('abrete Sezamo...', msg)
                if not UserIsBlocked(msg[2]):
                    if 'peatonal' in msg[1]:
                        print('execfile -> magnet.py')
                        #                         Activate()
                        magnet.Activate()
                    elif 'vehicular' in msg[1]:
                        print('execfile -> gate.py')
                        gate.Activate()
                    print('Apertura -->  ' + response + ', msh[1] -> [' + msg[1] + ']')
                else:
                    print('user blocked ...!!!!')
            elif msg[0] == 'status':
                sendStatus = True
                signal_Status()
            elif msg[0] == 'active_codes':
                sendSMS('active codes: ' + pkgListCodes())
        elif '+CSQ:' in response:
            pos = response.index(':')
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

            if sendStatus:
                sendStatus = False
                gsm_status.append({'Local': getLocalTimestamp()})
                gsm_status.append({'CBC': response_return})
                pcbTemp = getBoardTemp()
                gsm_status.append({'Temp': pcbTemp})
                #  --- send status  -------
                sendSMS(str(gsm_status) + '\n Codes: ' + pkgListCodes()
                        + '\n blocked: ' + pkgListAccess())

            elif debugging:
                print('CBC : ', response_return)
        # return (response_return)
        elif '+CGREG:' in response:
            pos = response.index(':')
            response_return = response[pos + 4: (pos + 4) + 1]
            cgreg_status = response_return
        # if cgreg_status != '1':
        # sim800Rst()
        # time.sleep(50)
        elif 'OVER-VOLTAGE' in response:  # 4.27v
            sendStatus = True
            if debugging:
                print('Aguas que se quema el modulo!!')
            gsm.write('AT+CBC\r')
        elif 'UNDER-VOLTAGE' in response:  # 3.48v
            sendStatus = True
            if debugging:
                print('Aguas que se enfria el modulo!!')
            gsm.write('AT+CBC\r')
    # except NameError:
    #     print('Error -->', NameError)
    #     pass


# endregion ------ Timers  -----------------------------------


def signal_Status():
    global gsm_status
    gsm_status = []
    gsm.write('AT+CSQ\r')
    utime.sleep(0.7)
    gsm.write('AT+CBC\r')
    utime.sleep(0.7)


def UserIsBlocked(uuid):
    restraint_list = {}
    jaccess = open("restraint.json", "r")
    restraint_list = json.loads(jaccess.read())
    for i, item in enumerate(restraint_list['user']):
        if (uuid.strip() == item['uuid']):
            return True
    return False




def sendSMS(msg):
    for i, item in enumerate(admin_sim):
        print('sent sms to ' + item)
        utime.sleep(1)
        gsm.write('AT+CMGS="' + item + '"\r\n')
        utime.sleep(1)
        gsm.write(str(msg) + "\r\n")

        gsm.write('\x1A')  # Enable to send SMS
        utime.sleep(1)
        # gsm.write(chr(26))
        # utime.sleep(0.5)


    # for i, item in enumerate(admin_sim):
    #     print('sent sms to ' + item)
    #     utime.sleep(1)
    #     gsm.write('AT+CMGS="' + str(item, encoding) + '"\r')
    #     utime.sleep(1)
    #     gsm.write(str(msg) + "\r")
    #
    #     # gsm.write('\x1A')  # Enable to send SMS
    #     utime.sleep(1)
    #     gsm.write(chr(26))
    #     utime.sleep(0.5)


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
        access = access + item['name'] + '-[' + item['house'] + '],'
    return access

# --- Verify if sim card is inserted ---
def simInserted():
    gsm.write('AT+CREG?\r')
    utime.sleep(0.7)


# endregion ------  functions --------------------------------------------------


# region  ----------------    Open CODES JSON files  --------------------

code = ''
code_hide = ''

try:
    jcodes = open('codes.json')
    code_list = json.loads(jcodes.read())

except OSError:  # Open failed
    print('Error--> ', OSError)
#     insertJson('','codes.json')
#endregion ---------------------------------------------------

# region ----------------    Open ACCESS JSON files   --------------------


try:
    jaccess = open('restraint.json')
    restraint_list = json.loads(jaccess.read())

except OSError:  # Open failed
    print('Error--> ', OSError)
#     insertJson('','codes.json')

# endregion  -----------------------------

#
# cleanCodes(1, '')  # -- clean by date
# codesAvailable()
# print("codes count  --- > ", len(code_list['codes']))

# ---  Check  GSM module sim ------
if simInserted() == "0":
    if debugging:
        print('Modulo GSM no tiene sim..!')
    oled1.fill(0)
    oled1.text("No SIM", 10, 15)
    oled1.show()
else:

    led25 = Pin(25, Pin.OUT)
    tim25 = Timer()

    # Initialize and set all the rows to low
    InitKeypad()
    #-------  SETUP GSM device  -------------------
    init_gsm()


    # Initialize timer Used for polling keypad
    timerKeypad = Timer()

    # Initialize timer used for sim800L
    timerSim800L = Timer()

    if debugging:
        tim25.init(freq=2, mode=Timer.PERIODIC, callback=tick25)

    timerSim800L.init(freq=2, mode=Timer.PERIODIC, callback=simResponse)
    # _thread.start_new_thread(simResponse, ())

    timerKeypad.init(freq=2, mode=Timer.PERIODIC, callback=PollKeypad)

    # ------ Timestamp section   ---------------------
    rtc = RTC()
    rtc_date = RTC().datetime()

    initial()
    print('Time after --> ' + str(utime.time()))
    song('initial')


