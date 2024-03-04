import json
########################################################
# mov       -> movement i:insert, d:delete, c:change
# file      -> json file name to update
# key       -> key to find
# value     -> value to change
# newValue  -> new value to change previous value
# Desc: Generic Module [crud] for JSON files
#######################################################33
def updJson(mov,file,key,value,newValue):
    global jcodes
    global code_list
    global restraint_list
    global config
    global openByCode
    try:
        jsonObj = open(file, "r")
        file_list = json.loads(jsonObj.read())
        jsonObj.close()
        for item in file_list:
            if item == key:
                if mov == 'r': #read
                    if file_list[item][key] == value:
                        print('si existe key -->',item, ', with value -> ', value)
                        break
                elif mov == 'd':   # delete
                    print('Delete action pending key -->',item,' : ',file_list[key],' with --> ', value)
                    break
                elif mov == 'i':   # insert
                    file_list[key].append(value)
                    jfiles = open(file,'w')
                    json.dump(file_list,jfiles)
                    jfiles.close()
                    break
                elif mov == 'c':   # change
                    file_list[key][value] = newValue
                    f = open(file,"w")
                    json.dump(file_list, f)
                    f.close()
                    break
                break
            for j, jitem in enumerate(file_list[item]):
                if jitem == key:
                    if mov == 'r':   # read
                        print('Read action pending key --> ',jitem,' : ',file_list[item][key],' with --> ', value)
                        break
                    elif mov == 'd':   # delete
                        print('Delete action pending key --> ',jitem,' : ',file_list[item][key],' with --> ', value)
                        break
                    elif mov == 'i':   # insert
                        print('Insert action pending key -> ',jitem,' : ',file_list[item],' with --> ', value)
                        break
                    elif mov == 'c':   # change
                        print('file_list[jitem]  -> ', file_list[jitem]);
                        print('upd action key, value, newValue -> ', key,', ', value, ', ', newValue);
                        file_list[jitem] = value
                        f = open(file,"w")
                        json.dump(file_list, f)
                        f.close()
                        break

                if type(jitem) == 'str':
                    for k,kitem in enumerate(file_list[item][jitem]):
                        print('kitem -> ', kitem)
                        if kitem == key:
                            if mov == 'r':   # Read
                                print('Read action pending kitem -->',kitem,' : ',file_list[item][jitem][key],' with --> ', value)
                                break
                            elif mov == 'd':   # delete
                                print('Delete action pending kitem -->',kitem,' : ',file_list[item][jitem][key],' with --> ', value)
                                break
                            elif mov == 'i':   # insert
                                print('Insert action pending kitem -->',kitem,' : ',file_list[item][jitem][key],' with --> ', value)
                                break
                            elif mov == 'c':   # change
                                print('Change action pending kitem -->',kitem,' : ',file_list[item][jitem][key],' with --> ', value)
                                break
                            break

                elif (type(jitem) != 'int' or type(jitem) != 'float' or type(jitem) != 'str') :
                    for l,dict in enumerate(jitem):
                        if dict == key and jitem[dict] == value:
                            if newValue == '':
                                if mov == 'r':   #read
                                    return True
                                    break
                                elif mov == 'd':   # delete
                                    del file_list[item][j]
                                    f = open(file,"w")
                                    json.dump(file_list, f)
                                    f.close()

                                    break
                                elif mov == 'i':   # insert
                                    print('Insert action pending index:', j, ' jitem -> ',file_list[item][j])
                                    break
                                elif mov == 'c':   # change
                                    print('Change action pending index:', j, ' jitem -> ',file_list[item][j])
                                    break
                            else:
                                for m, e in enumerate(file_list[item]):
                                    if e[key] == value and mov == 'c':
                                        print('last upd action key, value, newValue -> ', key,', ', value, ', ', newValue);
                                        file_list[item][m][key] = newValue
                                        f = open(file,"w")
                                        json.dump(file_list, f)
                                        f.close()
                                        break

            if file == 'codes.json':
                jcodes = open('codes.json')
                code_list = json.loads(jcodes.read())
                jcodes.close()
            elif file == 'restraint.json':
                jfiles = open('restraint.json')
                restraint_list = json.loads(jfiles.read())
                jfiles.close()
            elif file == 'config.json':
                jfiles = open('config.json')
                config = json.loads(jfiles.read())
                jfiles.close()
                openByCode = config['app']['openByCode']

    except FileNotFoundError as exc:  # create file not exists
        print('InsertJson Error --> ', file, ', ', FileNotFoundError)
        pass    
if __name__ == "__main__" :
    print("Running at tools.py")