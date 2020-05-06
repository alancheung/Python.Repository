try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")

GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)

print("Mode configured!")
pin = 37
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
try:
    while True:
        if GPIO.input(pin):
            print("High")
        else:
            print("Low")
except KeyboardInterrupt:
    print("KeyboardInterrupt caught! Cleaning up...")
    GPIO.cleanup()
    print("GPIO.cleanup() called!")
