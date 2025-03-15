import json
timestamp = ''

########################################################
# mov       -> movement c:crate, r:read, u:update, d:delete, updLock: lock user, updUnlock:unlock user
# file      -> json file name to update
# key       -> key to find
# value     -> value to change
# newValue  -> new value to change previous value
# wholeWord -> If Find whole word or part of it, default True [yes find whole word]
# return key-> return value from key, default = '' ignore return key, return '' if key not exist
#              used in updSim call like new Sim
# timestamp -> timestamp to update current value
# Desc: Generic Module [crud] for JSON files
#######################################################33
def updJson(mov, file, key, value = '' , newValue = '', wholeWord = True, returnKey = '', timestamp = ''):
    global jcodes
    global code_list
    global restraint_list
    global config
    global openByCode
    global debugging
    global found
    global level
    found = False
    level = 0

    try:
        jfiles = open('config.json')
        config = json.loads(jfiles.read())
        jfiles.close()
        debugging = config['app']['debugging']
        del config

        jsonObj = open(file)
        file_list = json.loads(jsonObj.read())
        jsonObj.close()

        for i,item in enumerate(file_list):
            # if file == 'restraint.json':
            #     if len(file_list) > 0 :
            #         print('last restraint: ', file_list[item][-1])
            
            if item == key:
                # Level one interaction, receiving just key without value
                if value == '':
                    if mov == 'c':
                        file_list[item].append(newValue)
                        f = open(file,"w")
                        json.dump(file_list, f)
                        f.close()
                        if debugging :
                            showData(file,key,value,mov)
                        break

                    elif mov == 'd':   # delete

                        #Verifying if file is already empty
                        if len(file_list[item]) == 0:
                            if file == "nfc.json":
                                if debugging:
                                    print('Initializing nfc.json file')
                                file_list = {"tags" : []}
                                break

                        if debugging :
                            print('Item deleting --> ', file_list[item])

                        del file_list[item]
                        f = open(file,"w")
                        if file == 'events.json' or file == 'extrange.json':
                            file_list = {"events" : []}

                        json.dump(file_list, f)
                        f.close()

                        break

                for j, jitem in enumerate(file_list[item]):
                    # json item is string
                    if type(jitem) is str:
                        if len(jitem) == len(value):
                            print('entre is str jsonTools jitem:{}, value: {} '.format(jitem,value))
                            if jitem == value:
                                found = True
                                level = 1
                            else:
                                if len(jitem) < len(value):
                                    if jitem in value:
                                        found = True
                                        level = 1
                                else:
                                    if value in jitem:
                                        found = True
                                        level = 1
                        
                          # when jitem found as array  -------------------------------------------
                    elif (type(jitem) is not int or type(jitem) is not float or type(jitem) is not str) :
                        if type(jitem[value]) is str:
                            if len(jitem[value]) == len(newValue):
                                if jitem[value] == newValue:
                                    found = True
                                    level = 2
                                else:
                                    if len(jitem[value]) < len(newValue):
                                        if jitem[value] in newValue:
                                            found = True
                                            level = 2
                                    else:
                                        if newValue in jitem[value]:
                                            found = True
                                            level = 2

                    if found:
                        if mov == 'updStatus_lock' or mov == 'updStatus_unlock':
                            if mov == 'updStatus_lock':
                                status = 'lock'
                            elif mov == 'updStatus_unlock':
                                status = 'unlock'

                            jitem['status'] = status
                            jitem['updatedAt'] = timestamp
                            wfile = open(file,'w')
                            json.dump(file_list, wfile)
                            wfile.close()
                            break

                        if mov == 'updSim':
                            jitem['sim'] = returnKey # parameter used only for this option like newSim
                            jitem['updatedAt'] = timestamp
                            wfile = open(file,'w')
                            json.dump(file_list, wfile)
                            wfile.close()
                            break                            

                        # if newValue == '': # not require change value
                        if mov == 'r':   # Read
                            if returnKey:
                                if level == 1:
                                    return file_list[item][returnKey]
                                elif level == 2:
                                    return jitem[returnKey]
                            else:
                                return True
                        elif mov == 'd':   # delete
                            if level == 1:
                                 #Verifying if file is already empty
                                if len(file_list[item]) == 0:
                                    if file == "nfc.json":
                                        if debugging:
                                            print('Initializing nfc.json file')
                                        file_list = {"tags" : []}
                                        break
                                
                                if (value != ''):
                                    if debugging :
                                        print('Item deleted --> ', file_list[item][j])
                                    del file_list[item][j]
                                else :
                                    if debugging :
                                        print('Item deleted --> ', file_list[item])
                                    del file_list[item]
                                    
                                f = open(file,"w")
                                json.dump(file_list, f)
                                f.close()
                                
                                break
                            elif level == 2:
                                if debugging :
                                    print('Item deleted --> ', file_list[item][j])
                                del file_list[item][j]
                                f = open(file,"w")
                                json.dump(file_list, f)
                                f.close()
                                
                                break
                        elif mov == 'c':   # create up to one level
                            file_list[item][value].append(newValue)
                            f = open(file,"w")
                            json.dump(file_list, f)
                            f.close()
                            if debugging :
                                showData(file,key,value,mov)
                            break
                        elif mov == 'u':   # update
                            if level == 1:
                                file_list[item][value] = newValue
                                f = open(file,"w")
                                json.dump(file_list, f)
                                f.close()
                                if debugging :
                                    showData(file,key,value,mov)
                                break
                            if level == 2:
                                print('file_list[item][value]: ', file_list[item][value] )
                                file_list[item][value] = newValue
                                f = open(file,"w")
                                json.dump(file_list, f)
                                f.close()
                                break
                  
                if mov != 'r':                                
                    if file == 'codes.json':
                        jcodes = open('codes.json')
                        code_list = json.loads(jcodes.read())
                        jcodes.close()
                        return
                    elif file == 'restraint.json':
                        jfiles = open('restraint.json', 'r')
                        restraint_list = json.loads(jfiles.read())
                        jfiles.close()
                        return
                    elif file == 'config.json':
                        jfiles = open('config.json')
                        config = json.loads(jfiles.read())
                        jfiles.close()
                        openByCode = config['app']['openByCode']
                        return
        
        

    except (TypeError) as err:  # create file not exists
        print('InsertJson Error --> ', file, ', ', err)
        pass

def showData(file,key,value = '', mov = 'r'):
    jsonObj = open(file)
    jsonlist = json.loads(jsonObj.read())
    jsonObj.close()
    mo = mov
    for i,item in enumerate(jsonlist):
        for j, jitem in enumerate(jsonlist[item]):
            if item == key:
                if value == '':
                    if mov == 'c':
                        if debugging:
                            print('Item added --> ', jsonlist[item][-1])
                    else:
                        if debugging:
                            print('data changed --> ', jitem)
                    break
                else:
                    if mov == 'c':
                        if debugging:
                            print('Item added --> ', jsonlist[item][-1])
                    elif mov == 'r':
                        if jsonlist[item].get(value) is not None:
                            return value + ' : ' + str(jsonlist[item][value])
                        else:
                            return 'item not exists'
                    else:
                        if debugging:
                            print('data changed --> ', jsonlist[item])
                    break


def getLocalTimestamp():
    global timestamp
    tsf = ((str(timestamp[0:2]) + '-' + str(timestamp[3:5]) + '-' +
          str(timestamp[6:8]) + 'T' + str(timestamp[9:11]) + ':' +
          str(timestamp[12:14]) + ':' + str(timestamp[15:17])))
    return tsf



if __name__ == "__main__" :
    print("Running jsonTools.py locally")
