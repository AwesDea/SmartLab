# RPi with DHT and LED
import time 
import RPi.GPIO as GPIO 
import paho.mqtt.client as mqtt 
# Configuration: 
LED_PIN = 0
# Initialize GPIO for LED and button. 
GPIO.setmode(GPIO.BCM) 
GPIO.setup(LED_PIN, GPIO.OUT) 
GPIO.output(LED_PIN, GPIO.LOW) 
# Setup callback functions that are called when MQTT events happen like 
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

