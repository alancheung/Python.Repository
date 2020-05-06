from __future__ import print_function
from datetime import datetime, time

#ignore = False
#start = datetime.now()
#while (datetime.now() - start).seconds < 30 and ignore is False:
#    print(f"running with {(datetime.now()- start).seconds}")
#    ignore = ignore or (datetime.now() - start).seconds == 1
#    print(f"{ignore}")
#print (f"done: {ignore}")

 # listen for awhile to determine if this is a freak disconnect
while True:
    freakDisconnect = False
    start = datetime.now()
    while freakDisconnect == False and (datetime.now() - start).seconds < 2:
        isDoorOpen = 0
        freakDisconnect = isDoorOpen

    # done listening, should I turn off lights?
    if freakDisconnect == True:
        print(f"Ignoring close event because of sensor reset in {(datetime.now() - start).seconds}s!", True)
    else:
        print("close()")
        break