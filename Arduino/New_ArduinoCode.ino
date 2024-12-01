#include <ArduinoJson.h>
#include <Arduino.h>
#include <SoftwareSerial.h>
#include <DHT.h>
#include <NewPing.h>

#define DHTPIN 2
#define DHTTYPE DHT11
#define PELTIER_PIN 3
#define HUMIDIFIER_PIN 4
#define ULTRASONIC_TRIGGER_PIN 5
#define ULTRASONIC_ECHO_PIN 6
#define WATER_PUMP_PIN 7
#define EXHAUST_PIN 8
#define HEATER_PIN 9
#define RELAY A5

#define MQ135_PIN A0 // mq135
#define co2zero 55

float lowTemp = 0;
float highTemp = 0;
float lowHumid = 0;
float highHumid = 0;
float lowCo2 = 0;
float highCo2 = 0;
float percentage = 0;

byte customMac[] = {0x00, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE};
DHT dht(DHTPIN, DHTTYPE);
NewPing ultrasonic(ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN);
int waterLevel;

//int fanPin = 7;


// ***** FOR MQ135 ******
#include <MQ135.h> // Include MQ135 library if available (optional for better accuracy)
//float RLOAD = 10.0;       // Load resistance on the board (in kilo-ohms)
//float RZERO = 76.63;      // Reference resistance in clean air (kilo-ohms)
//float PARA = 116.6020682; // Coefficient A for CO2 curve equation
//float PARB = 2.769034857; // Coefficient B for CO2 curve equation

float getResistance(int adcValue) {
  return ((1023.0 / (float)adcValue) - 1.0) * RLOAD;
}

float getPPM(float resistance) {
  return PARA * pow((resistance / RZERO), -PARB);
}
// ***** END FOR MQ135 ******


void setup()
{
  dht.begin(9600);
  Serial.begin(9600);
  pinMode(PELTIER_PIN, OUTPUT);
  pinMode(HUMIDIFIER_PIN, OUTPUT);
  pinMode(WATER_PUMP_PIN, OUTPUT);
  pinMode(EXHAUST_PIN, OUTPUT);
  
  //pinMode(fanPin, OUTPUT);
  //digitalWrite(fanPin, HIGH);

  pinMode(MQ135_PIN,INPUT);
}

bool isMQ135Connected() {
  // Set A0 as digital input to clear floating state
  pinMode(MQ135_PIN, OUTPUT);
  digitalWrite(MQ135_PIN, LOW); // Pull to ground
  
  // Wait briefly to stabilize the pin
  delay(10);

  // Set back to analog mode and read the value
  pinMode(MQ135_PIN, INPUT);
  int adcValue = analogRead(MQ135_PIN);
//  Serial.println("adcValue: " + String(adcValue));

  // Check if the analog value is consistently in a reasonable range
  // Floating pins typically give values that fluctuate widely
//  if (adcValue > 50 && adcValue < 1000) { 
//    delay(10); // Short delay to confirm stable reading
//    int adcValueCheck = analogRead(MQ135_PIN);
//    if (abs(adcValue - adcValueCheck) < 10) { // Verify stability
//      return true;
//    }
//  }
  if(adcValue != 0) return true;
  
  return false;
}

void loop()
{
//  delay(2000);
  // Change State of Fan and Heater
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Read command string until newline
//    Serial.println("command: " + command);
    if (command == "fanH") { // If command is 'H', set pin HIGH
      digitalWrite(EXHAUST_PIN, HIGH);
//      Serial.println("FAN ON");
    } else if (command == "fanL") { // If command is 'L', set pin LOW
      digitalWrite(EXHAUST_PIN, LOW);
//      Serial.println("FAN OFF");
    } else if (command == "heaterH") { // If command is 'H', set pin HIGH
      digitalWrite(HEATER_PIN, HIGH);
//      Serial.println("Heater ON");
    } else if (command == "heaterL") { // If command is 'L', set pin LOW
      digitalWrite(HEATER_PIN, LOW);
//      Serial.println("Heater OFF");
    }
  }


  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if ((isnan(temperature) || isnan(humidity)) || !isMQ135Connected())
  {
    if (!isMQ135Connected() && !(isnan(temperature) || isnan(humidity))) {
    Serial.println("MQ135 sensor not detected or not functioning!");
  //    delay(1000); // Wait and retry
  //    return;
    } else if(isMQ135Connected() && (isnan(temperature) || isnan(humidity))) {
      Serial.println("DHT sensor not detected or not functioning!"); //, TMP: " + String(temperature) + " HUM: " + String(humidity));
    } else {
      Serial.println("DHT and sensor MQ135 are not detected or not functioning!");
    }
    
    delay(1000);
    return;
  }

  humidity += -5.0;
  waterLevel = ultrasonic.ping_cm();

  // FOR MQ135
  int MQ135sensorValue = analogRead(MQ135_PIN); // Read analog value
  float resistance = getResistance(MQ135sensorValue); // Calculate resistance
  float ppm = getPPM(resistance); // Calculate CO2 concentration (ppm)

  delay(1000);

//    Serial.print("Temperature: ");
//    Serial.print(temperature);
//    Serial.print("Humidity: ");
//    Serial.print(humidity);
//    Serial.print("Water Levell: ");
//    Serial.println(waterLevel);
//    Serial.print("LVL: ");
//
//    Serial.print("Peltier: ");
//    Serial.println((temperature > 30) ? "ON" : "OFF");
//
//    Serial.print("Humidifier: ");
//    Serial.println((humidity < 80) ? "ON" : "OFF");
//
//    Serial.print("Water Pump: ");
//    Serial.println((waterLevel <= 30) ? "ON" : (waterLevel >= 95) ? "OFF" : "N/A");

  StaticJsonDocument<200> jsonDoc;
  jsonDoc["temperature"] = temperature;
  jsonDoc["humidity"] = humidity;
  jsonDoc["waterLevel"] = waterLevel;
  jsonDoc["co2ppm"] = round(ppm);

  String jsonString;
  serializeJson(jsonDoc, jsonString);

  Serial.println("JSON data: " + jsonString);

  delay(1000);
}
