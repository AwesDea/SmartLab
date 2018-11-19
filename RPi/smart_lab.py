# RPi  code
import time 
import RPi.GPIO as GPIO 
import paho.mqtt.client as mqtt
import SimpleMFRC522
import Adafruit_CharLCD as LCD
import threading
import logging
import Adafruit_DHT
import pandas as pd
import numpy as np
import datetime
#import matplotlib.pyplot as plt

# Configuration:


# Initialize GPIOs

GPIO.setmode(GPIO.BCM)

#setting lcd pins
lcd_rs        = 3
lcd_en        = 4
lcd_d4        = 14
lcd_d5        = 15
lcd_d6        = 17
lcd_d7        = 18
lcd_backlight = 27
lcd_columns   = 16
lcd_rows      = 2

#initiating lcd
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

#setting card reader
reader = SimpleMFRC522.SimpleMFRC522()

#setting MQTT LED PIN
MQTT_LED_PIN = 1

# LOCK PINS
LOCK_FIRST_PIN = 22
LOCK_SECOND_PIN = 23




# Data managment
def get_notification_history():
    try:
        notification_history = pd.read_pickle('notifications history')  #sensor sent notifications  stored in notification_history.
    except:
        notification_history = pd.DataFrame({'date':[datetime.datetime.now()],'sensor':[np.nan],'message':['hello world!']})
        notification_history.set_index('date', inplace=True)
        notification_history.to_pickle('notifications history')
    return notification_history

def get_door_lock_history():
    try:
        door_lock_history = pd.read_pickle('door lock history')  #door lock sent datas  stored in door_lock_history.
    except:
        door_lock_history = pd.DataFrame({'date':[datetime.datetime.now()], 'ID':[np.nan], 'response':[np.nan]})
        door_lock_history.set_index('date', inplace=True)
        door_lock_history.to_pickle('door lock history')
    return door_lock_history
def save_door_lock_history(df):
    df.to_pickle('door lock history')

def get_smoke_history():
    try:
        smoke_history = pd.read_pickle('smoke history')  #smoke sent datas  stored in smoke_history.
    except:
        smoke_history = pd.DataFrame({'date':[datetime.datetime.now()], 'smoke':[np.nan]})
        smoke_history.set_index('date', inplace=True)
        smoke_history.to_pickle('smoke history')
    return smoke_history

def get_dht_history():
    try:
        dht_history = pd.read_pickle('dht history')  #DHT sent datas  stored in dht_history.
    except:
        dht_history = pd.DataFrame({'date':[datetime.datetime.now()], 'temp':[np.nan], 'humidity':[np.nan]})
        dht_history.set_index('date')
        dht_history.to_pickle('dht history')
    return dht_history

def get_lamp_history():
    try:
        lamp_history = pd.read_pickle('lamp history')  #lamp sent datas  stored in lamp_history.
    except:
        lamp_history = pd.DataFrame({'date':[datetime.datetime.now()],'command':[np.nan]})
        lamp_history.set_index('date', inplace=True)
        lamp_history.to_pickle('lamp history')
    return lamp_history

def get_fan_history():
    try:
        fan_history = pd.read_pickle('fan history')  #fan sent datas stored in fan_history.
    except:
        fan_history = pd.DataFrame({'date':[datetime.datetime.now()],'command':[np.nan]})
        fan_history.set_index('date', inplace=True)
        fan_history.to_pickle('fan history')
    return fan_history

def get_IR_history():
    try:
        IR_history = pd.read_pickle('IR history')  #IR sent datas stored in IR_history.
    except:
        IR_history = pd.DataFrame({'date':[datetime.datetime.now()],'command':[np.nan]})
        IR_history.set_index('date', inplace=True)
        IR_history.to_pickle('IR history')
        return IR_history

##print(door_lock_history)
##print(lamp_history)
##print(notification_history)
##print(fan_history)
##print(dht_history)
##print(smoke_history)
##print(IR_history)

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
        lcd_messaging(lcd_lock,msg.payload)

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
        if ir_msg == b'16203967':
            client.publish('/esp1/fan', 'off')

        # For turning Fan ON
        elif ir_msg == b'16236607':
            client.publish('/esp1/fan', 'low')
        
        # FAN SPEED #
        
        # For speed 1 Fan
        elif ir_msg == b'16191727':
            client.publish('/esp1/fan', 'low')
        
        # For speed 2 Fan
        elif ir_msg == b'16224367':
            client.publish('/esp1/fan', 'medium')
        
        # For speed 3 Fan
        elif ir_msg == b'16208047':
            client.publish('/esp1/fan', 'high')
        
        # LAMP #
        
        # For turning Lamp ON
        elif ir_msg == b'16187647':
            client.publish('/esp2/lamp', 'on')
            
        # For turning Lamp OFF
        elif ir_msg == b'16220287':
            client.publish('/esp2/lamp', 'off')

        # For toggling the Lamp
        elif ir_msg == b'16238647':
            client.publish('/esp2/lamp', 'toggle')
        
        # LCD BACKLIGHT #
        
        # For toggling LCD Backlight
        elif ir_msg == b'16240687':
            lh = GPIO.input(lcd_backlight)
            print(lh)
            if lh == GPIO.HIGH:
                GPIO.output(lcd_backlight,GPIO.LOW)
                print('Backlight Off!')
            elif lh == GPIO.LOW:
                GPIO.output(lcd_backlight,GPIO.HIGH)
                print('Backlight ON!')

        
    #DHT sends tempreture details to the "/pi/dht" topic    
    elif msg.topic == '/pi/dht':
        lcd_messaging(lock, msg.payload)
    
    #Smoke sends smoke details to the "/pi/smoke" topic    
    elif msg.topic == '/pi/smoke':
        lcd_messaging(lock, msg.payload)
        
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


# locks lcd and write the message
def lcd_messaging(lock, message):
    #logging.debug('want to clear before messaging')
    lcd_clearing(lock)
    lock.acquire()
    try:
        lcd.message(message)
    except KeyboardInterrupt:
        pass
    finally:
        lock.release()


def lcd_clearing(lock):
    
    lock.acquire()
    try:
        lcd.clear()
        lock.release()
    except KeyboardInterrupt:
        pass
    finally:
        pass


#open the door nfc tags
def doorLock(lock):
    try:
        while(True):
            id, text = reader.read()
            date = datetime.datetime.now() #time of reading a card!
            print(id,text)
            #getting the door lock history dataframe
            door_lock_history = get_door_lock_history()

            #we saved the id from a random card and use that or another card to get granted or denied access you can change it in order to use ur own RFID card
            if id == 489637981035:
                print('Access Granted')
                
                #save the action in the dataframe
                df = pd.DataFrame({'date':[date], 'ID':[id], 'response':['Granted']})
                df.set_index('date',inplace=True)
                door_lock_history = door_lock_history.append(df)
                save_door_lock_history(door_lock_history)
                lcd_messaging(lock, 'Access Granted')
                # we saved a text (name of the owner of the card in this case on the rfid card
                print('Hello ' + text)
                time.sleep(1) #message stays on LCD fo 1 sec
                lcd_clearing(lock)
                #lcd_messaging(lock,last_message)

            else:
                print('Access Denied')
                df = pd.DataFrame({'date':[date], 'ID':[id], 'response':['Denied']})
                df.set_index('date',inplace=True)
                door_lock_history = door_lock_history.append(df)
                save_door_lock_history(door_lock_history)
                lcd_messaging(lock, 'Access Denied')
                time.sleep(1)
                lcd_clearing(lock)
                #lcd_messaging(lock,last_message)


    except KeyboardInterrupt:
        pass
    finally:
        pass


def ask_for_temp_feddback():
    client.publish('/esp3/dht', 'feedback')

        

lcd_last_message = 'Good Luck!'
lcd_lock = threading.Lock()
##nfc = threading.Thread(target=doorLock, args=(lcd_lock,), name='NFC Reader')
##nfc.daemon = True
##
##try:
##    nfc.start()
##    nfc.join()
##finally:
##    pass
##while True:
doorLock(lcd_lock)
print(get_door_lock_history())


