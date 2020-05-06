from lifxlan import LifxLAN
from datetime import datetime, time
from time import sleep
import sys
import json

#print(datetime.now().time())
#if datetime.now().time() <= time(16, 33, 0, 0):
#    print("Yes")
#else:
#    print("No")
WARM_WHITE = [58112, 0, 65535, 2500]
DAYLIGHT = [58112, 0, 65535, 5500]

def lightOnSequence(now, s, e):
    if is_between_time(now, (s, e)):
            officeLightGroup.set_color(DAYLIGHT, rapid = True)
    else:
        officeLightGroup.set_color(WARM_WHITE, rapid = True)

    try:
        print("One on!")
        officeOne.set_power("on", duration=5000)
        sleep(1)
        print("Two on!")
        officeTwo.set_power("on", duration=4000)
        sleep(1)
        print("Three on!")
        officeThree.set_power("on", duration=3000)
        sleep(1)
    except:
        print("Exception ocurred.")

lifx = LifxLAN(7)
officeLightGroup = lifx.get_devices_by_group("Office")
officeLights = officeLightGroup.get_device_list()
officeOne = lifx.get_devices_by_name("Office One")
officeTwo = lifx.get_devices_by_name("Office Two")
officeThree = lifx.get_devices_by_name("Office Three")

if len(officeLights) < 3:
    print(f"Did not discover all office lights! ({len(officeLights)} of 3)")
    devices = lifx.get_lights()
    print("\nFound {} light(s):\n".format(len(devices)))
    for d in devices:
        try:
        	print(d)
        except:
            pass
    sys.exit(-1)

def is_between_time(time, time_range):
    if time_range[1] < time_range[0]:
        return time >= time_range[0] or time <= time_range[1]
    return time_range[0] <= time <= time_range[1]

def convert_time(timestring):
    return datetime.strptime(timestring, "%H:%M").time()

timestones = None
try:
    with open("./timestones.json") as file:
        timestones = json.load(file)
    work_morning_start = convert_time(timestones["work_morning_start"])
    work_morning_end = convert_time(timestones["work_morning_end"])
    afternoon_dimmer = convert_time(timestones["afternoon_dimmer"])
except FileNotFoundError:
    err("timestones.json could not be found!")
finally:
    file.close()

print(timestones)

s = convert_time(timestones["work_morning_start"])
e = convert_time(timestones["work_morning_end"])
m = time(8, 44, 0, 0, datetime.now().tzinfo)

#lightOnSequence(m, s, e)