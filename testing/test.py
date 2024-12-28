import jsonTools
import datetime
import json

current_datetime = datetime.datetime.now()
timestampSec = current_datetime.timestamp()
# print("Timestamp:", timestampSec)


def getLocalTimestamp():
    global timestamp
    tsf = ((str(timestamp[0:2]) + '-' + str(timestamp[3:5]) + '-' +
          str(timestamp[6:8]) + 'T' + str(timestamp[9:11]) + ':' +
          str(timestamp[12:14]) + ':' + str(timestamp[15:17])))
    return tsf

timestamp = datetime.datetime.fromtimestamp(timestampSec).strftime("%y-%m-%d %H:%M:%S")
# print("Formatted Timestamp:", timestamp)
# print('timestamp: ', getLocalTimestamp())

conf = open('config.json')
config = json.loads(conf.read())
conf.close()


code_list = {}
jcodes = open('codes.json')
code_list = json.loads(jcodes.read())
jcodes.close()

restraint = open('restraint.json')
restraint_list = json.loads(restraint.read())
restraint.close()

role = jsonTools.updJson('r', 'restraint.json','user','sim', '+526641752182',True,'role')
print('role: ', role)
# Check extrange sender----------------------------------
if not jsonTools.updJson('r', 'restraint.json','user','sim', '+526641752182',False):
    print('Extrange attempted')


if role == 'admin':

    print('Returned --> ', jsonTools.showData('config.json','app','openByCode','r'))
# Codes -------------
    # api_data = {"userId": '1234567890', "date": getLocalTimestamp(),
    #                         "code": '123ABC', "visitorSim": '+526641752182',
    #                         "codeId": '1234567890'}
    # jsonTools.updJson('c', 'codes.json','codes', '', api_data)



   

    # jsonTools.updJson('d','codes.json','codes','codeId','1234567890')

# restraint  ----------------------------

    # jsonTools.updJson('updSim', 'restraint.json','user','sim', '+5266417521822',
    #                 False,'5266417521823',getLocalTimestamp())

    # api_data = { "name": "testing", "house": "14", "sim": "+5266417521823",
    # "status": "unlock","id": "1234567890", "role": "neighbor",
    # "lockedAt": getLocalTimestamp()}
    # jsonTools.updJson('c', 'restraint.json','user', '', api_data, '')

    # jsonTools.updJson('d','restraint.json','user','id','1234567890')

    # jsonTools.updJson('updSim', 'restraint.json','user','sim', '+5266417521824',
    #                                    False, '+5266417521825', getLocalTimestamp())
    
     
    # jsonTools.updJson('updStatus_lock', 'restraint.json','user','sim', '+5266417521825',
    #                 False,'',getLocalTimestamp())

    # jsonTools.updJson('updStatus_unlock', 'restraint.json','user','sim', '+526641752182',
    #                 False,'',getLocalTimestamp())


# config  ----------------------------
    
    # jsonTools.updJson('u','config.json','app', 'rotate', True)
    # jsonTools.updJson('u','config.json','app', 'openByCode', 'gate')
    # jsonTools.updJson('u','config.json','app', 'rotate', True)
    # jsonTools.updJson('u','config.json','keypad_matrix', 'default', 'hardPlastic')
    # jsonTools.updJson('u','config.json','keypad_matrix', 'default', 'flex')
    # jsonTools.updJson('u','config.json','sim', 'sendCodeEvents', True)