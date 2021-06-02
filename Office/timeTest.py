import json
from datetime import datetime, time, timedelta
lightConfigs = None

def log(text, displayWhenQuiet = False):
    now = datetime.now().strftime("%x %X")
    message = f"{now}: {text}"
    print(message)

def is_between_time(time_to_check, start, end):
    if start > end:
        if time_to_check >= start or time_to_check < end:
            return True
    elif start < end:
        if time_to_check >= start and time_to_check < end:
            return True
    elif time_to_check == start:
        return True
    return False

def convert_time(timestring):
    return datetime.strptime(timestring, "%H:%M").time()

def get_light_sequence(now):
    # Get the first config where 
    #       the current time is between the start and end 
    #       the current day is not excluded
    config = next((c for c in lightConfigs if is_between_time(now, convert_time(c["StartTime"]), convert_time(c["EndTime"])) and (5 in c["ExcludedDays"]) == False), None)

    if config is None:
        log("Could not find a valid light sequence at {now.strftime('%x %X')}!")
    else:
        log(f"Found config at {now.strftime('%x %X')} with description {config['Description']}")
    return config

try:
    with open("path/light-config.json") as configFile:
        lightConfigs = json.load(configFile)
        log("File loaded!")
except FileNotFoundError:
    log("'/home/pi/Project/light-config.json' could not be found!")
    sys.exit(-1)


get_light_sequence(convert_time("08:00"))
get_light_sequence(convert_time("09:00"))
get_light_sequence(convert_time("10:00"))
get_light_sequence(convert_time("16:30"))
get_light_sequence(convert_time("17:30"))
get_light_sequence(convert_time("22:00"))
get_light_sequence(convert_time("22:34"))
get_light_sequence(convert_time("23:00"))
get_light_sequence(convert_time("00:00"))
get_light_sequence(convert_time("02:00"))
get_light_sequence(convert_time("03:00"))
get_light_sequence(convert_time("04:39"))
get_light_sequence(convert_time("05:00"))

