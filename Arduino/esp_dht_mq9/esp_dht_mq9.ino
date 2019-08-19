//ESP 3 with DHT11 & MQ9

#include <ESP8266WiFi.h>
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include "DHT.h"

/************************* WiFi Access Point *********************************/
#define WLAN_SSID       "Smart Lab"
#define WLAN_PASS       "amints25"

#define MQTT_SERVER      "192.168.0.100" // ip address of rpi
#define MQTT_PORT         1883
#define MQTT_USERNAME    ""
#define MQTT_PASSWORD         ""



//
/************ Global State ******************/
#define DHT_PIN      2              // Pin connected to the IR. GPIO 0
#define A0    0              // Pin connected to the lamp. GPIO 2 
#define DHT_TYPE DHT11  // for DHT model == DHT 11


// Create an ESP8266 WiFiClient class to connect to the MQTT server.
WiFiClient client;
// Setup the MQTT client class by passing in the WiFi client and MQTT server and login details.
Adafruit_MQTT_Client mqtt(&client, MQTT_SERVER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD);
/****************************** Feeds ***************************************/
// Setup a feeds for publishing.

// Notice MQTT paths for AIO follow the form: <username>/feeds/<feedname>
Adafruit_MQTT_Publish pi_lcd = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/lcd");                   //give rpi messages for printing
Adafruit_MQTT_Publish pi_notif = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/notif");               //give rpi notifications
Adafruit_MQTT_Publish pi_dht_mq9 = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/dht_mq9");               //give rpi notifications

// Setup a feed for subscribing to changes.
Adafruit_MQTT_Subscribe esp_dht_mq9 = Adafruit_MQTT_Subscribe(&mqtt, MQTT_USERNAME "/esp3/dht_mq9");            // get messages for dht

/*************************** Sketch Code ************************************/

uint32_t x = 0;

int timer = 0;

void MQTT_connect();

//DHT
DHT dht(DHT_PIN, DHT_TYPE);
String sh;
String st;
String dht_string = "Nothing stored untill now from DHT!";


//status
String status_string = dht_string;


void setup() {
  Serial.begin(115200);

  Serial.println(F("RPi-ESP3-MQTT"));
  
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
  mqtt.subscribe(&esp_dht_mq9);

  //Start DHT
  dht.begin();
  pi_notif.publish("KIIIIIIIIR.");            


}

void loop() {
  
  /* Ensure the connection to the MQTT server is alive (this will make the first
  connection and automatically reconnect when disconnected).  See the MQTT_connect*/
  MQTT_connect();
  /* this is our 'wait for incoming subscription packets' busy subloop try to spend your time here*/
  pi_notif.publish("koooooos.");            

  /************* DHT code: *************/
  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  float temp = dht.readTemperature();

  if (isnan(h) || isnan(temp)) {
    Serial.println("Failed to read from DHT sensor!");
    dht_string = "Failed to read from DHT sensor!";
  } else {

    st = String(temp);
    sh = String(h);
    dht_string = "Humidity: " + sh + " % " + "Temperature: " + st + " *C ";
    //Serial.println(dht_string);
  }


  /*----------------------------------Adding-------------------------------------*/
  status_string = dht_string;
  char status_char_array[status_string.length() + 1];
  status_string.toCharArray(status_char_array, status_string.length() + 1 ); 


  /**************** MQTT subscription code: ****************/
  // Here its read the subscription
  Adafruit_MQTT_Subscribe *subscription;
  while ((subscription = mqtt.readSubscription())) {
    if (subscription == &esp_dht_mq9) {
      char *message = (char *)esp_dht_mq9.lastread;
      Serial.print(F("Got: "));
      Serial.println(message);
      // Check if the message feedback.
      if (strncmp(message, "feedback", 8) == 0) {
        
        pi_dht_mq9.publish(status_char_array);

      }
    }
  }

  
   pi_dht_mq9.publish(status_char_array);

    //Wait for 2 seconds before starting another temp and smoke getting
  delay(2000);

}



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
    pi_notif.publish("ESP3 MQTT connected.");
}
