# RPi  code
import time 
import RPi.GPIO as GPIO 
import paho.mqtt.client as mqtt
import SimpleMFRC522
import Adafruit_CharLCD as LCD
import threading
import logging
import Adafruit_DHT
# Configuration:

# Initialize GPIOs
GPIO.setmode(GPIO.BCM)

#setting lcd pins
lcd_rs        = 21
lcd_en        = 20
lcd_d4        = 16
lcd_d5        = 13
lcd_d6        = 19
lcd_d7        = 26
lcd_backlight = 2
lcd_columns   = 16
lcd_rows      = 2

#initiating lcd
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

#setting card reader
reader = SimpleMFRC522.SimpleMFRC522()

# setting IR receiver
IR_pin = 12



# Setup callback functions that are  called when MQTT events happen like 
# connecting to the server or receiving data from a subscribed feed. 
def on_connect(client, userdata, flags, rc): 
   print("Connected with result code " + str(rc)) 
   # Subscribing in on_connect() means that if we lose the connection and 
   # reconnect then subscriptions will be renewed. 
   client.subscribe("/leds/pi") 
   client.subscribe("/lcd/pi") 

# The callback for when a PUBLISH message is received from the server. 
def on_message(client, userdata, msg): 
    print(msg.topic+" "+str( msg.payload)) 
   # Check if this is a message for the Pi LED. 
    if msg.topic == '/leds/pi': 
       # Look at the message data and perform the appropriate action. 
       if msg.payload == b'on': 
           GPIO.output(LED_PIN, GPIO.HIGH) 
       elif msg.payload == b'off': 
           GPIO.output(LED_PIN, GPIO.LOW)
           
    elif msg.topic == '/lcd/pi':
        print(msg.payload)
# Create MQTT client and connect to localhost, i.e. the Raspberry Pi running 
# this script and the MQTT server. 
client = mqtt.Client() 
client.on_connect = on_connect 
client.on_message = on_message 
client.connect('localhost', 1883, 60) 
# Connect to the MQTT server and process messages in a background thread. 
client.loop_start() 
# Main loop to listen for button presses. 
print('Script is running, press Ctrl-C to quit...')
try:
    while True:
        pass
finally:
    GPIO.cleanup()

