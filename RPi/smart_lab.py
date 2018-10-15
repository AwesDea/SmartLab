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

# Data managment
notification_history = [] #notifications stored here. type: (notif message, time)
dht_history = [] #DHT sensor datas stored here. type: (temp,humidity,time)
smoke_history = [] #smoke sensor datas stored here. type: (smoke,time)
door_lock_history = [] # Door lock datas stored here. type: (card_id,access_response,time)
lamp_history = [] # Lamp datas stored here. type: (lamp_command,time)
fan_history = [] # Fan datas stored here. type: (fan_status,time)
ir_history = [] # IR commands datas stored here. type: (ir_command,time)

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

#setting MQTT LED PIN
MQTT_LED_PIN = 1

# LOCK PINS
LOCK_FIRST_PIN = 2
LOCK_SECOND_PIN = 3

# Setup callback functions that are  called when MQTT events happen like 
# connecting to the server or receiving data from a subscribed feed. 
def on_connect(client, userdata, flags, rc): 
   print("Connected with result code " + str(rc)) 
   # Subscribing in on_connect() means that if we lose the connection and 
   # reconnect then subscriptions will be renewed. 
   client.subscribe("/pi/lcd") 
   client.subscribe("/pi/lock")
   client.subscribe("/pi/mqtt led")
   client.subscribe("/pi/ir")
   client.subscribe("/pi/notif")

# The callback for when a PUBLISH message is received from the server. 
def on_message(client, userdata, msg): 
    print(msg.topic+" "+str( msg.payload)) 
   # Check if this is a message for the Pi LED. 
    if msg.topic == '/pi/mqtt led': 
       # Look at the message data and perform the appropriate action. 
       if msg.payload == b'on': 
           GPIO.output(MQTT_LED_PIN, GPIO.HIGH) 
       elif msg.payload == b'off': 
           GPIO.output(MQTT_LED_PIN, GPIO.LOW)
           
    elif msg.topic == '/pi/lcd':
        lcd.message(msg.payload)

        # all notifications from any device are stored here and printed in rpi console.    
    elif msg.topic == '/pi/notif':
        print("Notification Received but nothing gonna happen")
        
    elif msg.topic == '/pi/lock':
        
        # For locking the door
        if msg.payload == b'LOCK':
            # Make it 1 0 for locking
            GPIO.output(LOCK_FIRST_PIN, GPIO.HIGH)
            GPIO.output(LOCK_SECOND_PIN, GPIO.LOW)
            # Make it 0 0 for doing nothing after setting the last operation being completed
            time.sleep(2)
            GPIO.output(LOCK_FIRST_PIN, GPIO.LOW)
            GPIO.output(LOCK_FIRST_PIN, GPIO.LOW)
        
        # For unlocking the door
        if msg.payload == b'UNLOCK':
            # Make it 0 1 for locking
            GPIO.output(LOCK_FIRST_PIN, GPIO.LOW)
            GPIO.output(LOCK_SECOND_PIN, GPIO.HIGH)
            # Make it 0 0 for doing nothing after setting the last operation being completed
            time.sleep(2)
            GPIO.output(LOCK_FIRST_PIN, GPIO.LOW)
            GPIO.output(LOCK_FIRST_PIN, GPIO.LOW)
        
        
    elif msg.topic == '/pi/ir':
        
        # FAN #
        
        ir_msg = msg.payload
        # For turning Fan OFF
        if ir_msg == b'D4DD0381':
            client.publish('/esp1/fan', 'off')

        # For turning Fan ON
        elif ir_msg == b'F7C03F':
            client.publish('/esp1/fan', 'low')
        
        # FAN SPEED #
        
        # For speed 1 Fan
        elif ir_msg == b'F710EF':
            client.publish('/esp1/fan', 'low')
        
        # For speed 2 Fan
        elif ir_msg == b'6471EC7D':
            client.publish('/esp1/fan', 'medium')
        
        # For speed 3 Fan
        elif ir_msg == b'9D52009D':
            client.publish('/esp1/fan', 'high')
        
        # LAMP #
        
        # For turning Lamp ON
        elif ir_msg == b'8503705D':
            client.publish('/esp2/lamp', 'on')
            
            pass#turn on lamp
        # For turning Lamp OFF
        elif ir_msg == b'DEB0C861':
            client.publish('/esp2/lamp', 'off')
            pass# lamp
        # For toggling the Lamp
        elif ir_msg == b'F7C837':
            client.publish('/esp2/lamp', 'toggle')
            pass#turn off lamp
        
        # LCD BACKLIGHT #
        
        # For toggling LCD Backlight
        elif ir_msg == b'F7D02F':
            if lcd_backlight == GPIO.HIGH:
                GPIO.output(lcd_backlight,Low)
            else:
                 GPIO.output(lcd_backlight,HIGH)   
        
    #DHT sends tempreture details to the "/pi/dht" topic    
    elif msg.topic == '/pi/dht':
        get_temp_feedback(lock,last_message, msg.payload)
        
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


#needs to lock lcd
def lcd_messaging(lock, message):
    #logging.debug('want to clear before messaging')
    lcd_clearing(lock)
    lock.acquire()
    try:
        print('In lock for messaging.')
        lcd.message(message)
    except KeyboardInterrupt:
        print('Finished in messaging')
    finally:
        lock.release()
        print('Lock released after messaging.')


def lcd_clearing(lock):
    
    lock.acquire()
    try:
        print('In lock for clearing.')
        lcd.clear()
        lock.release()
    except KeyboardInterrupt:
        print('Finished in clearing')
    finally:
        print('Lock released after clearing.')


#open the door nfc tags
def doorLock(lock):
    try:
        while(True):
            id, text = reader.read()
            #we saved the id from a random card and use that or another card to get granted or denied access you can change it in order to use ur own rfid card
            if id == 489637981035:
                print('Access Granted')
                lcd_messaging(lock, 'Access Granted')
                # we saved a text (name of the owner of the card in this case) on the rfid card
                print('Hello ' + text)
                time.sleep(1) #wainting fo 1 sec
                lcd_clearing(lock)
        	lcd_messaging(lock,last_message)
            else:
                print('Access Denied')
                lcd_messaging(lock, 'Access Denied')
                time.sleep(1)
                lcd_clearing(lock)
        	lcd_messaging(lock,last_message)

    except KeyboardInterrupt:
        print('Finished')
    finally:
        print('finished')

def get_temp_feedback(lock,last_message, temp_feedback):
    try:
        lcd_messaging(lock,last_message)
        
        last_message = temp_feedback
        print(last_message)
        lcd_messaging(lock,last_message)
    except KeyboardInterrupt:
        print('Finished Temping')
    finally:
        print('finished temping')

def ask_for_temp_feddback():
    client.publish('/esp3/dht', 'feedback')

        

lcd_last_message = 'Good Luck!'
lcd_lock = threading.Lock()
nfc = threading.Thread(target=doorLock, args=(lcd_lock,), name='NFC Reader')
nfc.daemon = True

temp = threading.Thread(target=get_temp_feedback, args=(lcd_lock,lcd_last_message, ), name='Tempreture Reader')
temp.daemon = True
try:
    nfc.start()
    temp.start()
    temp.join()
    nfc.join()



finally:
    pass


