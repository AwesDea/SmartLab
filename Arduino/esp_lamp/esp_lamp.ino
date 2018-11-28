//ESP 2 with Lamp & IR

#include <ESP8266WiFi.h>
#include <IRrecv.h>
#include <IRutils.h>
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
/************************* WiFi Access Point *********************************/
#define WLAN_SSID       "Smart Lab"
#define WLAN_PASS       "amints25"

#define MQTT_SERVER      "192.168.0.100" // ip address of rpi
#define MQTT_PORT         1883
#define MQTT_USERNAME    ""
#define MQTT_PASSWORD         ""



//
/************ Global State ******************/
#define IR      2              // Pin connected to the IR. GPIO 0
#define LAMP    0              // Pin connected to the lamp. GPIO 2 



// Create an ESP8266 WiFiClient class to connect to the MQTT server.
WiFiClient client;
// Setup the MQTT client class by passing in the WiFi client and MQTT server and login details.
Adafruit_MQTT_Client mqtt(&client, MQTT_SERVER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD);
/****************************** Feeds ***************************************/
// Setup a feeds for publishing.

// Notice MQTT paths for AIO follow the form: <username>/feeds/<feedname>
Adafruit_MQTT_Publish pi_mqtt_led = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/mqtt led");   //checking mqtt connection for rpi
Adafruit_MQTT_Publish pi_lcd = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/lcd");             //give rpi messages for printing
Adafruit_MQTT_Publish pi_ir = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/ir");               // publish ir commands for rpi to handle
Adafruit_MQTT_Publish pi_notif = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/notif");         //give rpi notifications

// Setup a feed for subscribing to changes.
Adafruit_MQTT_Subscribe esp_lamp = Adafruit_MQTT_Subscribe(&mqtt, MQTT_USERNAME "/esp2/lamp");        // get messages for Lamp
/*************************** Sketch Code ************************************/

void MQTT_connect();

IRrecv irrecv(IR);

decode_results results;

void setup()
{
  Serial.begin(9600);   // you can comment this line
  irrecv.enableIRIn();  // Start the receiver
  pinMode(LAMP, OUTPUT);

  Serial.println(F("RPi-ESP2-MQTT"));
  // Connect to WiFi access point.
  Serial.println(); Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WLAN_SSID);
  WiFi.begin(WLAN_SSID, WLAN_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi connected");
  Serial.println("IP address: "); Serial.println(WiFi.localIP());
  // Setup MQTT subscription for feeds.
  mqtt.subscribe(&esp_lamp);



}

void loop() {

  //********************  TODO set mqtt feedback for rpi  ***************************


  // Ensure the connection to the MQTT server is alive (this will make the first
  // connection and automatically reconnect when disconnected).  See the MQTT_connect
  MQTT_connect();
  // this is our 'wait for incoming subscription packets' busy subloop


  // check for IR response
  if (irrecv.decode(&results)) {
    unsigned int value = results.value;
    pi_ir.publish(value);//send ir received value to rpi
    irrecv.resume(); // Receive the next value
  }


  // Here its read the subscription
  Adafruit_MQTT_Subscribe *subscription;
  while ((subscription = mqtt.readSubscription())) {
    if (subscription == &esp_lamp) {
      char *message = (char *)esp_lamp.lastread;
      Serial.print(F("Got: "));
      Serial.println(message);
      // Check if the message was off, on or toggle.
      if (strncmp(message, "off", 3) == 0) {
        digitalWrite(LAMP, LOW);
        pi_notif.publish("esp_lamp Turned OFF");
      }
      else if (strncmp(message, "on", 2) == 0) {
        digitalWrite(LAMP, HIGH);
        pi_notif.publish("esp_lamp Turned ON");

      }
      else if (strncmp(message, "toggle", 6) == 0) {
        if (digitalRead(LAMP) == HIGH) {
          digitalWrite(LAMP, LOW);
          pi_notif.publish("esp_lamp Toggled and Turned OFF");
        }
        else if (digitalRead(LAMP) == LOW) {
          digitalWrite(LAMP, HIGH);
          pi_notif.publish("esp_lamp Toggled and Turned ON");
        }
      }
    }
  }


}


// Function to connect and reconnect as necessary to the MQTT server.

void MQTT_connect() {
  int8_t ret;
  // Stop if already connected.
  if (mqtt.connected()) {
    return;
  }
  Serial.print("Connecting to MQTT... ");
  uint8_t retries = 3;
  while ((ret = mqtt.connect()) != 0) { // connect will return 0 for connected
    Serial.println(mqtt.connectErrorString(ret));
    Serial.println("Retrying MQTT connection in 5 seconds...");
    mqtt.disconnect();
    delay(5000);  // wait 5 seconds
    retries--;
    if (retries == 0) {
      // basically die and wait for WDT to reset me
      while (1);
    }
  }
  Serial.println("MQTT Connected!");
}
