try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")

try:
    GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers
 
    RELAY_GPIO = 4
    GPIO.setup(RELAY_GPIO, GPIO.OUT) # GPIO Assign mode

    high = False
    while True:
        if high:
            input("GPIO set HIGH, press any key to set LOW")
            GPIO.output(RELAY_GPIO, GPIO.LOW) # out
        else:
            input("GPIO set LOW, press any key to set HIGH")
            GPIO.output(RELAY_GPIO, GPIO.HIGH) # on
        high = not high
except KeyboardInterrupt:
    GPIO.cleanup()
