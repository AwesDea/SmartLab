//ESP 3 with DHT & Smoke

#include <ESP8266WiFi.h>
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include "DHT.h"

/************************* WiFi Access Point *********************************/
#define WLAN_SSID       "Smart Lab"
#define WLAN_PASS       "amints25"

#define MQTT_SERVER      "192.168.43.101" // ip address of rpi
#define MQTT_PORT         1883
#define MQTT_USERNAME    ""
#define MQTT_PASSWORD         ""



//
/************ Global State ******************/
#define DHT_PIN      2              // Pin connected to the IR. GPIO 0
#define LAMP    0              // Pin connected to the lamp. GPIO 2 
#define DHT_TYPE DHT11  // for DHT model == DHT 11


// Create an ESP8266 WiFiClient class to connect to the MQTT server.
WiFiClient client;
// Setup the MQTT client class by passing in the WiFi client and MQTT server and login details.
Adafruit_MQTT_Client mqtt(&client, MQTT_SERVER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD);
/****************************** Feeds ***************************************/
// Setup a feeds for publishing.

// Notice MQTT paths for AIO follow the form: <username>/feeds/<feedname>
Adafruit_MQTT_Publish pi_mqtt_led = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/mqtt led");         //checking mqtt connection for rpi
Adafruit_MQTT_Publish pi_lcd = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/lcd");                   //give rpi messages for printing
Adafruit_MQTT_Publish pi_notif = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/notif");               //give rpi notifications
Adafruit_MQTT_Publish pi_dht = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/dht");               //give rpi notifications
Adafruit_MQTT_Publish pi_notif = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/pi/smoke");               //give rpi notifications

// Setup a feed for subscribing to changes.
Adafruit_MQTT_Subscribe esp_dht = Adafruit_MQTT_Subscribe(&mqtt, MQTT_USERNAME "/esp3/dht");            // get messages for dht
Adafruit_MQTT_Subscribe esp_smoke = Adafruit_MQTT_Subscribe(&mqtt, MQTT_USERNAME "/esp3/smoke");        // get messages for Lamp

/*************************** Sketch Code ************************************/

uint32_t x = 0;

int timer = 0;

void MQTT_connect();

//DHT
DHT dht(DHT_PIN, DHT_TYPE);
String sh;
String st;
String dht_string = "Nothing stored untill now!";

//Smoke
int sensorValue;
float sensor_volt;
float RS_gas; // Get value of RS in a GAS
float ratio; // Get ratio RS_GAS/RS_air
String smoke_string;


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
  mqtt.subscribe(&esp_smoke);
  mqtt.subscribe(&esp_dht);

  //Start DHT
  dht.begin();
}

void loop() {
  
  /* Ensure the connection to the MQTT server is alive (this will make the first
  connection and automatically reconnect when disconnected).  See the MQTT_connect*/
  MQTT_connect();
  /* this is our 'wait for incoming subscription packets' busy subloop try to spend your time here*/

  /************* DHT code: *************/
  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  float temp = dht.readTemperature();

  if (isnan(h) || isnan(temp)) {
    Serial.println("Failed to read from DHT sensor!");
  } else {

    st = String(temp);
    sh = String(h);
    dht_string = "Humidity: " + sh + " %\t" + "Temperature: " + st + " *C";
    //Serial.println(dht_string);
  }

  /************* Smoke code: *************/
  sensorValue = analogRead(A0);
  sensor_volt = (float)sensorValue / 1024 * 5.0;
  RS_gas = (5.0 - sensor_volt) / sensor_volt; // omit *RL

  //-0.09 was the value of R0 from the mq9 tester file
  ratio = RS_gas / -0.09; // ratio = RS/R0
  /*-----------------------------------------------------------------------*/
  smoke_string = "sensor_volt = " + String(sensor_volt) + "RS_ratio = " + String(RS_gas) + "Rs/R0 = " + String(ratio);
  //Serial.println(smoke_string);


  /**************** MQTT subscription code: ****************/
  // Here its read the subscription
  Adafruit_MQTT_Subscribe *subscription;
  while ((subscription = mqtt.readSubscription())) {
    if (subscription == &esp_smoke) {
      char *message = (char *)esp_smoke.lastread;
      Serial.print(F("Got: "));
      Serial.println(message);
      // Check if the message feedback.
      if (strncmp(message, "feedback", 8) == 0) {
        pi_notif.publish("esp_dht_smoke is sending Smoke response...");
        char smoke_char_array[smoke_string.length() + 1];
        smoke_string.toCharArray(smoke_char_array, smoke_string.length() + 1 );
        pi_smoke.publish(smoke_char_array);
      }
    }

    else if (subscription == &esp_dht) {
      char *message = (char *)esp_dht.lastread;
      Serial.print(F("Got: "));
      Serial.println(message);
      // Check if the message was for feedback
      if (strncmp(message, "feedback", 8) == 0) {
        pi_notif.publish("esp_dht_smoke is sending dht response...");
        char dht_char_array[dht_string.length() + 1];
        dht_string.toCharArray(dht_char_array, dht_string.length() + 1 );
        pi_dht.publish(dht_char_array);
      }
    }
  }
  //Wait for 2 seconds before starting another temp and smoke getting
  delay(2000);
  
  timer += 1;
  // each (t * 2) seconds sends feedback automatically
  int t = 5;
  if (timer % t == 0) {
    char dht_char_array[dht_string.length() + 1];
    dht_string.toCharArray(dht_char_array, dht_string.length() + 1 );
    pi_dht.publish(dht_char_array);

    char smoke_char_array[smoke_string.length() + 1];
    smoke_string.toCharArray(smoke_char_array, smoke_string.length() + 1 );
    pi_smoke.publish(smoke_char_array);
  }
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
  Serial.println("MQTT Connected!");
}
