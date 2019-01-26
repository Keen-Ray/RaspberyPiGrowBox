# This program is for a raspberry pi controlled grow box.
# With fans for cooling, a light for heat, 4 water sensors, and a thermometer.
# if there is a problem that the program detects it sends a text message to my phone
# imports
import RPi.GPIO as GPIO
import time
import glob
from twilio.rest import TwilioRestClient
import logging
import os


# define pins and other information
water_sensors = [2, 3, 17, 19]
fan = 22
thermometer = 4
water = 21  # this is the solenoid control pin
heat = 5  # this is the light bulb control pin
thresh_hold_temperature = 75  # if the temperature in the box is 10 less turn on heat if it is 10 more turn on the fans

# do some boiler plate setup


# set up the pins
GPIO.setmode(GPIO.BCM)  # this setting allows me to use numbers to refer to the GPIO pins
GPIO.setwarnings(False)  # helps the program not generate false errors
for sensor in water_sensors: # set all the water sensor pins as inputs
    GPIO.setup(sensor, GPIO.IN)
GPIO.setup(fan, GPIO.OUT)  # set the fan pin as an output
GPIO.setup(water, GPIO.OUT)  # set the sulenoid pin as an output
GPIO.setup(heat, GPIO.OUT)  # set the light blub pin as an output

# get the thermometer running I copied this code from adafruit
os.system("modprobe w1-gpio")  # commands to terminal to get the thermometer running
os.system("modprobe w1-therm")
base_dir = '/sys/bus/w1/devices/'  # these three lines set the file path for the temperature
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'
# Twilio setup, this is for making text messages get this information from your twilio account
account_sid = "ACf15d10f63afb6d7d24e5e2e1ee3831bd"
auth_token = "9681cd92ade54cac4100a857c17998b1"
client = TwilioRestClient(account_sid, auth_token)
my_phone_number = "+14023187432"
twilio_phone_number = "+13602343384"


def send_text(text_body):  # function called when I want to send a text to my phone
    message = client.messages.create(to=my_phone_number, from_=twilio_phone_number, body=text_body)

# setup logging
logging.basicConfig(filename="garden.log") # log the info to a file named garden.log
time_format = "%m/%d/%Y at %I:%M"  # mm/dd/YYYY at hour:minute is the format this creates

# Check the water sensors

while True:  # an unending loop to keep the program running forever.
    def are_any_water_sensors_dry(array_of_water_sensor): # this function checks all the water sensors
        for pin_number in array_of_water_sensor:  # loop though all the water sensors
            if GPIO.input(pin_number) == 1:  # is one of sensors dry
                logging.warning("water sensor: " + str(pin_number) + " does not have any water " +
                                time.strftime(time_format) + "/n")
                there_is_not_water = True
                break  # stop the for loop above and return that there is not water
            else:  # this sensor are wet
                there_is_not_water = False
        return there_is_not_water


    if are_any_water_sensors_dry(water_sensors):  # if any of the sensor are dry turn on the water for 1 minute
        GPIO.output(water, GPIO.HIGH)  # turn on the pin that controls the solenoid
        time.sleep(60)  # wait for a minute
        GPIO.output(water, GPIO.LOW)  # turn off the water
        time.sleep(180)  # wait for the water to soak in and check the sensor again
        logging.info("plants were watered at " + time.strftime(time_format) + "/n")  # log that the plants were watered
        if are_any_water_sensors_dry(water_sensors):
            # check the sensors again if they are not wet something is wrong with the sensor or the watering system
            send_text("One of the water sensor is not getting water")  # send a warning that the water is not coming
            logging.error("the plants aren't getting water" + time.strftime(time_format) + "/n")
    else:
        logging.info("all water_sensors are wet " + time.strftime(time_format) + "/n")  # replace
    logging.info("test")

    # check the temperature

    def read_temp_raw():  # read the file containing temperature copied from adafruit
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines


    def read_temp():  # read the temperature copied from adafruit
        lines = read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':  # check if the temperature is being read and read the next line
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_f

    temperature_original = read_temp()  # get the temperature
    temperature = temperature_original
    while temperature > thresh_hold_temperature + 10:  # if the temperature is more than 10 degrees above the thresh hold
        GPIO.output(fan, GPIO.HIGH)  # turn on the fan
        time.sleep(240)  # 4 min
        temperature = read_temp()
        if temperature_original == temperature or temperature_original < temperature:
            send_text("The fans aren't keeping the box cool enough")
            logging.error("the fans can't keep up because the temperature was: " + str(temperature_original) + " " +
                          time.strftime(time_format) + "/n")
        GPIO.output(fan, GPIO.LOW)
        logging.info("The fans ran because the temperature was " + str(temperature_original) + " " +
                     time.strftime(time_format) + "/n")

    while temperature < thresh_hold_temperature - 10:  # if the temperature is more than 10 degrees below the thresh hold
        GPIO.output(heat, GPIO.HIGH)  # turn on the light
        time.sleep(120)  # 2 min
        temperature = read_temp()
        if temperature_original == temperature or temperature_original > temperature:
            send_text("the light can't keep the box hot enough")
            logging.error("it's too cold help! the temperature was: " + str(temperature_original) + " " +
                          time.strftime(time_format) + "/n")
        GPIO.output(heat, GPIO.LOW)
        logging.info("The light turned on because the temperature was:" + str(temperature_original) + " " +
                     time.strftime(time_format) + "/n")
    time.sleep(120)
print("script stopped")
GPIO.cleanup()
