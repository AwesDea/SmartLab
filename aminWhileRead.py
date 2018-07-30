#!/usr/bin/env python

import RPi.GPIO as GPIO
import SimpleMFRC522
import Adafruit_CharLCD as LCD
import time



#rfid id = 990032143682
#nfc id = 489637981035
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

GPIO.setmode(GPIO.BCM)
GPIO.setup(18,GPIO.OUT) # Green LED
GPIO.setup(17,GPIO.OUT) # Red LED

try:
    while(True):
        id, text = reader.read()
        if id == 489637981035:
            print('Access Granted')
            lcd.message('Access Granted')
            print('Hello ' + text)
            GPIO.output(18,GPIO.HIGH)
            time.sleep(1) #wainting fo 1 sec
            GPIO.output(18,GPIO.LOW)
            lcd.clear()
        else:
            print('Access Denied')
            lcd.message('Access Denied')
            #GPIO.setmode(GPIO.BCM)
            GPIO.setup(17,GPIO.OUT) # Red LED
            GPIO.output(17,GPIO.HIGH)
            time.sleep(1)
            GPIO.output(17,GPIO.LOW)
            lcd.clear()
except KeyboardInterrupt:
    print('Finished')
finally:
    GPIO.cleanup()

            
