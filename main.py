from micropython import const
from machine import UART, Pin, I2C, Timer, RTC, ADC, PWM, reset
import _thread
from ssd1306 import SSD1306_I2C
# from umqtt.simple import MQTTClient
import json
import utime
import magnet
import gate
import initSetup

#####6 git branch alert_open_event  -----------------

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
coreId = config['app']['coreId']
show_code = config['app']['show_code']
buzzer_pin = config['pi_pins']['buzzer']
version_app = config['app']['version']

# ----- Intialization -----------
buzzer = PWM(Pin(buzzer_pin))
if debugging:
    print('Version ' + version_app)
initSetup.Initial()

# ------------------ Setup GSM -----------------------
gsm_tx = config['pi_pins']['gsm_TX']
gsm_rx = config['pi_pins']['gsm_RX']
gsm_baud = config['sim']['serial_baud']
encoding = 'utf-8'
# gsm = UART(0, 9600, tx=Pin(gsm_tx), rx=Pin(gsm_rx), rxbuf=512)
gsm = UART(0, gsm_baud, tx=Pin(gsm_tx), rx=Pin(gsm_rx))

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
apn = config['sim']['apn']
app_version = config['app']['app_version']
serial_port = config['sim']['serial_port']
serial_baud = config['sim']['serial_baud']
serial_timeout = config['sim']['serial_timeout']
HTTPACTION_waitTime = config['sim']['HTTPACTION_waitTime']
api_get_line = config['sim']['api_get_line']
incoming_calls = config['sim']['incoming_calls']


# region ----------  show command received ------------------
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

# endregion

# region -------- Configuration  -------------------------------------
def alterConfig(key1,key2,value):
    with open('config.json','r+',encoding ='utf8') as cfile:
        json_data = json.load(cfile)
        json_data[key1][key2] = value
        # cfile.seek(0)
    with open('config.json', 'w') as outFile:
        try:
            outFile.seek(0)
            json.dump(json_data,outFile)
            # outFile.truncate()
            print('Done alterConfig----------------')
        except OSError:
            print("Oops!", OSError, "occurred.")
            print("Next entry.")
            print()
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
# endregion  -----------------  Variable  ---------------------------

# region----- Functions --------------------

def ShowMainFrame():
    oled1.fill(0)
    oled1.text("* <-", 1, 0)
    oled1.text(Today[-2:], 45, 0)
    oled1.text('# enter', 75, 0)
    if len(active_codes) > 0:
        oled1.text("..", 1, 9)
    oled1.text("Codigo: ", 1, 22)
    oled1.show()


def initial():
    global sendStatus
    gsm.write('AT+CCLK?\r')
    # cleanup expired codes
    utime.sleep(5)

    cleanCodes(1, '')
    ShowMainFrame()
    # gsm_config_gprs()

    # send module status  ---------------
    sendStatus = True
    signal_Status('Reboot')


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


def softReset():
    reset()

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
    global restraint_list
    jaccess = open("restraint.json", "r")
    restraint_list = json.loads(jaccess.read())
    jaccess.close()

    for i, item in enumerate(restraint_list['user']):
        if item['uuid'] == uuid:
            del restraint_list['user'][i]
            f = open("restraint.json","w")
            json.dump(restraint_list, f)
            f.close()
            break

    jaccess = open("restraint.json", "r")
    restraint_list = json.loads(jaccess.read())
    jaccess.close()


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
                reg_code_event(str(item['codeId']))
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
    data = {"codeId": code_id, "picId": "NA", "CoreSim": config['sim']['value']}
    url = config['sim']['url'] + config['sim']['api_codes_events']
    jsonLen = len(str(data).encode('utf-8'))
    # gsm.write('AT+SAPBR=3,1,"Contype","GPRS"\r\n')
    # utime.sleep(1)

    # global keepMonitorSIM800L
    # instr = 'AT+SAPBR=3,1,"APN","%s"\r\n' % apn
    # gsm.write(instr.encode())
    # utime.sleep(1)

    # Enable bearer 1.

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

    # instr = 'AT+HTTPPARA="URL","%s"\r' % url
    # gsm.write(instr.encode())
    gsm.write('AT+HTTPPARA="URL","%s"\r' % url)
    utime.sleep(2)

    gsm.write('AT+HTTPPARA="CONTENT","application/json"\r')
    utime.sleep(2)


    gsm.write('AT+HTTPDATA=%s,5000\r' % str(jsonLen))
    utime.sleep(1.5)

    gsm.write(json.dumps(data) + '\r')
    utime.sleep(3.5)

    # 0 = GET, 1 = POST, 2 = HEAD
    gsm.write('AT+HTTPACTION=1\r')
    utime.sleep(5)

    gsm.write('AT+HTTPREAD\r')
    utime.sleep(2)

    gsm.write('AT+HTTPTERM\r')
    utime.sleep(1)

    gsm.write('AT+SAPBR=0,1\r')
    utime.sleep(1)

def alert_event(msg,title,subtitle):
    # line below its just to put some data into data variable but not used for message by itself
    data = {"msg":"message"}
    subUrl = config['sim']['url'] + config['sim']['api_alerts'] + coreId
    url = subUrl + '/' + msg + '/' + title + '/' + subtitle
    jsonLen = len(str(data).encode('utf-8'))
    # gsm.write('AT+SAPBR=3,1,"Contype","GPRS"\r\n')
    # utime.sleep(1)

    # global keepMonitorSIM800L
    # instr = 'AT+SAPBR=3,1,"APN","%s"\r\n' % apn
    # gsm.write(instr.encode())
    # utime.sleep(1)

    gsm.write('AT+SAPBR=1,1\r')
    utime.sleep(2)

    gsm.write('AT+SAPBR=2,1\r')
    utime.sleep(2)

    gsm.write('AT+HTTPINIT\r')
    utime.sleep(2)

    gsm.write('AT+HTTPPARA="CID",1\r')
    utime.sleep(2)

    # instr = 'AT+HTTPPARA="URL","%s"\r' % url
    # gsm.write(instr.encode())
    gsm.write('AT+HTTPPARA="URL","%s"\r' % url)
    utime.sleep(2)

    gsm.write('AT+HTTPPARA="CONTENT","application/json"\r')
    utime.sleep(2)


    gsm.write('AT+HTTPDATA=%s,5000\r' % str(jsonLen))
    utime.sleep(1.5)

    gsm.write(json.dumps(data) + '\r')
    utime.sleep(3.5)

    # 0 = GET, 1 = POST, 2 = HEAD
    gsm.write('AT+HTTPACTION=1\r')
    utime.sleep(5)

    gsm.write('AT+HTTPREAD\r')
    utime.sleep(2)

    gsm.write('AT+HTTPTERM\r')
    utime.sleep(2)

    gsm.write('AT+SAPBR=0,1\r')
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
                if MATRIX[row][col] == '*' and code != '00':
                    if len(code) > 0:
                        code = code[0:-1]
                        code_hide = code_hide[0:-1]
                elif MATRIX[row][col] == '#':
                    if len(code) > 5:
                        my_timer = 0
                        cleanCodes(1, '')
                        verifyCode(code)
                    elif code == '00*': # SOFT RESET
                        softReset()
                    elif len(code) > 0 and code == '00*0':
                        code = code_hide = ''
                        oled1.text("Codigo: ", 1, 22)
                    elif len(code) > 0 and code != '00*':
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
                oled1.fill(0)
                oled1.text("* <-", 1, 0)
                oled1.text(Today[-2:], 45, 0)
                oled1.text('# enter', 75, 0)
                if show_code:
                    oled1.text("Codigo: " + code, 1, 22)
                else:
                    oled1.text("Codigo: " + code_hide, 1, 22)
                if (len(active_codes) > 0):
                    oled1.text('..', 1, 9)
                oled1.show()
                last_key_press = MATRIX[row][col]
                if debugging:
                    print("Codigo:" + code)


def printHeader():
    oled1.fill(0)
    oled1.text("* <-", 1, 0)
    oled1.text(Today[-2:], 45, 0)
    oled1.text('# enter', 75, 0)
    if len(active_codes) > 0:
        oled1.text('..', 1, 9)


def getLocalTimestamp():
    global timestamp
    tsf = ((str(timestamp[0:2]) + '-' + str(timestamp[3:5]) + '-' +
          str(timestamp[6:8]) + 'T' + str(timestamp[9:11]) + ':' +
          str(timestamp[12:14]) + ':' + str(timestamp[15:17])))
    return tsf


# def send_data_to_broker(data):
#     print("Attempting to send data to broker")
#     max_mqtt_attempts = 5
#     attempts = 0
#     published = False
#     connected = False
#     while not published and attempts < max_mqtt_attempts:
#         try:
#             mqtt_client.connect()
#             connected = True
#             mqtt_client.publish('demo_pp', json.dumps(data))
#             mqtt_client.disconnect()
#             published = True
#             print("Data sent to broker")
#         except Exception as e:
#             print('Error at send data to broker --> ', e)
#             print('Attempt %s of %s' % attempts, max_mqtt_attempts)
#             if connected:
#                 mqtt_client.disconnect()
#                 connected = False
#             attempts += 1
#             utime.sleep(3)

def simResponse(timer):
    # def simResponse():
    global tupleToday
    global Today
    global gsm_status
    global sendStatus

    msg = ''
    # try:

    if gsm.any() > 0:
        response = str(gsm.readline(), encoding).rstrip('\r\n')
        if debugging:
            print(response)
        if 'ERROR' in response:
            print('Error detected')
        elif '+CREG:' in response:  # Get sim card status
            global simStatus
            # response = str(gsm.readline(), encoding).rstrip('\r\n')
            pos = response.index(':')
            simStatus = response[pos + 4: len(response)]
            showMsg(simStatus)
            if debugging:
                print('sim status --> ' + simStatus)
            return simStatus
        elif '+CCLK' in response:  # Get timestamp from GSM network
            global timestamp
            response = str(gsm.readline(), encoding).rstrip('\r\n')
            showMsg(response)
            if debugging:
                print('sim status --> ' + response)
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
            response = str(gsm.readline(), encoding).rstrip('\r\n')
            if 'twilio' in response.lower():
                msg = response.split("-")
                lenght = len(response)
                index = response.find('-')
                msg = response[index + 2:lenght].split(',')
            else:
                msg = response.split(",")
            if debugging:
                print('GSM Message: ' + response)

            # if msg[0].strip() == 'mqtt':
                # send_data_to_broker({'hello':'test'})

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

            elif msg[0].strip() == 'locked':
                if not verifyRestraint(msg[4]):
                    api_data = { "name": msg[1], "email": msg[2], "uuid": msg[3],
                                "house": msg[4].rstrip('\r\n'),
                                "local": getLocalTimestamp()}
                    insertJson(api_data, 'restraint.json')
            elif msg[0].strip() == 'unlocked':
                api_data = {"name": msg[1], "email": msg[2], "uuid": msg[3],
                            "house": msg[4].rstrip('\r\n'),
                            "date": getLocalTimestamp()}
                unblockUser(msg[3])
                # ----- Update available codes  -----
                #   print('Es un acceso --> ' + str(datetime.now()) + ' - ' + response)
            elif msg[0].strip() == 'open':
                if not UserIsBlocked(msg[2]):
                    if debugging:
                        print('Abriendo....', msg)
                        if 'peatonal' in msg[1]:
                            magnet.Activate()
                            alert_event("Apertura_Peatonal","title","subtitle")
                        elif 'vehicular' in msg[1]:
                            gate.Activate()
                            alert_event("Apertura_Vehicular","title","subtitle")
                else:
                    showMsg('User locked')
            elif msg[0] == 'status':
                sendStatus = True
                signal_Status('Status')
            elif msg[0] == 'active_codes':
                sendSMS('codes available --> ' + pkgListCodes())
            elif msg[0] == 'rst':
                alterConfig('app','debugging',False)
                showMsg('Reset')
                softReset()
            elif msg[0] == 'cfgCHG':
                alterConfig(msg[1], msg[2],msg[3])
            # elif msg[0] == 'post':
            #     reg_code_event('62f05aaffcc8845454760252', msg[1])

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
                gsm_status.append({']Local': getLocalTimestamp()})
                gsm_status.append({'CBC': response_return})
                pcbTemp = getBoardTemp()
                gsm_status.append({'Temp': pcbTemp})
                #  --- send status  -------
                sendSMS(str(gsm_status) + '\n Codes: ' + pkgListCodes()
                        + '\n locked: ' + pkgListAccess())
            elif debugging:
                print('CBC : ', response_return)
        # return (response_return)
        elif '+CGREG:' in response:
            pos = response.index(':')
            response_return = response[pos + 4: (pos + 4) + 1]
            cgreg_status = response_return
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


# endregion ------ Timers  -----------------------------------


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


