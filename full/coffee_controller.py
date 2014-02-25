import RPi.GPIO as GPIO
#TempSens
import os
import glob
import time

from time import gmtime, strftime
from flask import Flask, render_template, request
from celery.task.schedules import crontab
from celery.decorators import periodic_task
app = Flask(__name__)

GPIO.setmode(GPIO.BCM)

#Temp Sens
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# Create a dictionary called pins to store the pin number, name, and pin state:
pins = {
   17 : {'name' : 'Mr. Coffee', 'state' : GPIO.LOW}
   }

# Set each pin as an output and make it low:
for pin in pins:
   GPIO.setup(pin, GPIO.OUT)
   GPIO.output(pin, GPIO.LOW)

message = "Device ready for use"
time = strftime("%H:%M:%S", gmtime())
temp = 0

#Starting to setup task-scheduling using Celery
@periodic_task(run_every=crontab(hour=7, minute=30, day_of_week="mon"))
def scheduled_coffee():
    GPIO.output(17, GPIO.HIGH)


@app.route("/")
def main():
   # For each pin, read the pin state and store it in the pins dictionary:
   for pin in pins:
      pins[pin]['state'] = GPIO.input(pin)
   # Put the pin dictionary into the template data dictionary:
   templateData = {
      'pins' : pins,
      'time' : time,
      'message' : message,
	  'temp' : temp
      }
   # Pass the template data into the template main.html and return it to the user
   return render_template('main.html', **templateData)

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

# The function below is executed when someone requests a URL with the pin number and action in it:
@app.route("/<changePin>/<action>")
def action(changePin, action):
   # Convert the pin from the URL into an integer:
   changePin = int(changePin)
   # Get the device name for the pin being changed:
   deviceName = pins[changePin]['name']
   # If the action part of the URL is "on," execute the code indented below:
   if action == "checktemp":
	#When checking temp
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
		equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
   if action == "on":
      # Set the pin high:
      GPIO.output(changePin, GPIO.HIGH)
      # Save the status message to be passed into the template:
      message = "Spaceballs the coffee maker went to plaid "
      time = strftime("%H:%M:%S", gmtime())
   if action == "off":
      GPIO.output(changePin, GPIO.LOW)
      message = "Spaceballs the coffeemaker now off "
      time = strftime("%H:%M:%S", gmtime())
   if action == "toggle":
      # Read the pin and set it to whatever it isn't (that is, toggle it):
      GPIO.output(changePin, not GPIO.input(changePin))
      message = deviceName + " toggled"
      time = strftime("%H:%M:%S", gmtime())

   # For each pin, read the pin state and store it in the pins dictionary:
   for pin in pins:
      pins[pin]['state'] = GPIO.input(pin)

   # Along with the pin dictionary, put the message into the template data dictionary:
   templateData = {
      'message' : message,
      'pins' : pins,
	  'time' : time,
	  'temp' : temp_f
   }

   return render_template('main.html', **templateData)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)