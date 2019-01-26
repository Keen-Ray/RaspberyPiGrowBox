import RPi.GPIO as GPIO
import time
input_channel = 17
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(input_channel, GPIO.IN)
while True:
    if GPIO.input(input_channel) == 0
        print("Water!")
    else:
        print("No Water")

    time.sleep(10)
