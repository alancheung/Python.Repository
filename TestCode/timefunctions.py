#from __future__ import print_function
#from datetime import datetime, time

##ignore = False
##start = datetime.now()
##while (datetime.now() - start).seconds < 30 and ignore is False:
##    print(f"running with {(datetime.now()- start).seconds}")
##    ignore = ignore or (datetime.now() - start).seconds == 1
##    print(f"{ignore}")
##print (f"done: {ignore}")

# # listen for awhile to determine if this is a freak disconnect
#while True:
#    freakDisconnect = False
#    start = datetime.now()
#    while freakDisconnect == False and (datetime.now() - start).seconds < 2:
#        isDoorOpen = 0
#        freakDisconnect = isDoorOpen

#    # done listening, should I turn off lights?
#    if freakDisconnect == True:
#        print(f"Ignoring close event because of sensor reset in {(datetime.now() - start).seconds}s!", True)
#    else:
#        print("close()")
#        break

import os
import json
calibratedObj = {
    "DryValue": 6876786,
    "DryVoltage": 12.7832,
    "WetValue": 13.8796345343,
    "WetVoltage": 14.456786789
    }

jsonObj = json.dumps(calibratedObj)
print(jsonObj)

if os.path.isfile('./calibration.json'):
    with open("./calibration.json", "r+") as outputFile:
        data = outputFile.read()
        outputFile.seek(0)
        json.dump(calibratedObj, outputFile)
        outputFile.truncate()
else:
    with open("./calibration.json", "w") as outputFile:
        json.dump(calibratedObj, outputFile)



with open("./calibration.json") as timestoneFile:
    decodedObj = json.load(timestoneFile)
    print(str(decodedObj))

