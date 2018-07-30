#!/usr/bin/env python

import RPi.GPIO as GPIO
import SimpleMFRC522
import Adafruit_CharLCD as LCD
import time
import threading
import logging
import Adafruit_DHT


logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(messages)s',
                    )


GPIO.setmode(GPIO.BCM)

#setting DHT11 up
DHT_sensor_model = Adafruit_DHT.DHT11
DHT_sensor_pin = 23



#setting card reader
reader = SimpleMFRC522.SimpleMFRC522()


#setting lcd pins

lcd_rs        = 21  # Note this might need to be changed to 21 for older revision Pi's.
lcd_en        = 20
lcd_d4        = 16
lcd_d5        = 13
lcd_d6        = 19
lcd_d7        = 26
lcd_backlight = 2
lcd_columns = 16
lcd_rows    = 2

#initiating lcd
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

GPIO.setup(18,GPIO.OUT) # Green LED
GPIO.setup(17,GPIO.OUT) # Red LED


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


#nfc tags
def doorLock(lock):
    try:
        while(True):
            id, text = reader.read()
            if id == 489637981035:
                print('Access Granted')
                lcd_messaging(lock, 'Access Granted')
                print('Hello ' + text)
                GPIO.output(18,GPIO.HIGH)
                time.sleep(1) #wainting fo 1 sec
                GPIO.output(18,GPIO.LOW)
                lcd_clearing(lock)
        	lcd_messaging(lock,last_message)
            else:
                print('Access Denied')
                lcd_messaging(lock, 'Access Denied')
                GPIO.output(17,GPIO.HIGH)
                time.sleep(1)
                GPIO.output(17,GPIO.LOW)
                lcd_clearing(lock)
        	lcd_messaging(lock,last_message)

    except KeyboardInterrupt:
        print('Finished')
    finally:
        print('finished')
        pass

def get_temp(lock,last_message):
    try:
        lcd_messaging(lock,last_message)

        while True:
            print('temp start 2')


            humidity, temperature = Adafruit_DHT.read_retry(DHT_sensor_model, DHT_sensor_pin)
            print(temperature,humidity)
            if humidity is not None and temperature is not None:
                last_message = 'Temp={0:0.1f}*C\nHumidity={1:0.1f}%'.format(temperature, humidity)
                print(last_message)
                lcd_messaging(lock,last_message)
            else:
                print('Failed to get reading. Try again!')
    except KeyboardInterrupt:
        print('Finished Temping')
    finally:
        pass
        

lcd_last_message = 'Good Luck!'
lcd_lock = threading.Lock()
nfc = threading.Thread(target=doorLock, args=(lcd_lock,), name='NFC Reader')
nfc.daemon = True

temp = threading.Thread(target=get_temp, args=(lcd_lock,lcd_last_message, ), name='Tempreture Reader')
temp.daemon = True
try:
    nfc.start()
    temp.start()
    temp.join()
    nfc.join()



finally:
    pass
    #GPIO.cleanup()
