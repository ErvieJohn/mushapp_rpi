#include <ArduinoJson.h>
#include <Arduino.h>
#include <SoftwareSerial.h>
#include <DHT.h>
#include <NewPing.h>

#define DHTPIN 2
//#define DHTTYPE DHT11
#define DHTTYPE DHT22
#define PELTIER_PIN 3
#define HUMIDIFIER_PIN 11
#define ULTRASONIC_TRIGGER_PIN 5
#define ULTRASONIC_ECHO_PIN 6
#define WATER_PUMP_PIN 12
#define EXHAUST_PIN 8
#define HEATER_PIN 9
#define RELAY A5

// New
#define EXHAUST_PIN2 10

#define MQ135_PIN A1 // mq135
#define co2zero 55

DHT dht(DHTPIN, DHTTYPE);
NewPing ultrasonic(ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN);
int waterLevel;

//int fanPin = 7;


// ***** FOR MQ135 ******
#include <MQ135.h> // Include MQ135 library if available (optional for better accuracy)
// Define constants for CO2 calculation
#define RL 10.0  // Load resistance in kΩ (check your setup, usually 1kΩ or 10kΩ)
#define RZERO_CLEAN_AIR 1140.0  // Adjust based on your calibration

MQ135 mq135_sensor(MQ135_PIN);
// ***** END FOR MQ135 ******

// FOR Automatic and Manual
bool isAutomatic = true;

void setup()
{
  dht.begin();
  Serial.begin(9600);
  pinMode(PELTIER_PIN, OUTPUT);
  pinMode(HUMIDIFIER_PIN, OUTPUT);
  pinMode(WATER_PUMP_PIN, OUTPUT);
  pinMode(EXHAUST_PIN, OUTPUT);
  pinMode(EXHAUST_PIN2, OUTPUT);
  pinMode(HEATER_PIN, OUTPUT);
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

  if(adcValue != 0) return true;
  
  return false;
}

void loop(){
  // Change State of Fan, Heater, Humidifier, and Fan2
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');

    if (command == "auto"){
      isAutomatic = true;

      digitalWrite(EXHAUST_PIN, LOW);
      digitalWrite(HEATER_PIN, LOW);
      digitalWrite(HUMIDIFIER_PIN, LOW);
      digitalWrite(EXHAUST_PIN2, LOW);
      digitalWrite(WATER_PUMP_PIN, LOW);
      digitalWrite(PELTIER_PIN, LOW);

    } else if(command == "manual"){
      isAutomatic = false;

      digitalWrite(EXHAUST_PIN, LOW);
      digitalWrite(HEATER_PIN, LOW);
      digitalWrite(HUMIDIFIER_PIN, LOW);
      digitalWrite(EXHAUST_PIN2, LOW);
      digitalWrite(WATER_PUMP_PIN, LOW);
      digitalWrite(PELTIER_PIN, LOW);
    }

    if(!isAutomatic){
      if (command == "fanH") { 
        digitalWrite(EXHAUST_PIN, HIGH);
  
      } else if (command == "fanL") {
        digitalWrite(EXHAUST_PIN, LOW);
  
      } else if (command == "heaterH") { 
        digitalWrite(HEATER_PIN, HIGH);
  
      } else if (command == "heaterL") { 
        digitalWrite(HEATER_PIN, LOW);
  
      } else if (command == "humidifierH") { 
        digitalWrite(HUMIDIFIER_PIN , HIGH);
  
      } else if (command == "humidifierL") { 
        digitalWrite(HUMIDIFIER_PIN, LOW);
  
      } else if (command == "fan2H") { 
        digitalWrite(EXHAUST_PIN2, HIGH);
  
      } else if (command == "fan2L") {
        digitalWrite(EXHAUST_PIN2, LOW);
      } else if (command == "waterPumpH") { 
        digitalWrite(WATER_PUMP_PIN, HIGH);
  
      } else if (command == "waterPumpL") {
        digitalWrite(WATER_PUMP_PIN, LOW);
  
      } else if (command == "peltierH") { 
        digitalWrite(PELTIER_PIN, HIGH);
  
      } else if (command == "peltierL") {
        digitalWrite(PELTIER_PIN, LOW);
  
      }
    }
  }

  // VALUES
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  //humidity += -5.0;

  waterLevel = 20 - ultrasonic.ping_cm();//waterLvlValue();
  if(waterLevel == 20) waterLevel = 0;

  // FOR MQ135
  // Read resistance and calculate new RZero
  float resistance = mq135_sensor.getResistance();
  float rzero = resistance / exp((log10(400.0) - 1.78) / -2.93);  // Using CO2 calibration formula
  float correctedRZero = mq135_sensor.getCorrectedRZero(temperature, humidity);

  // Calculate CO2 PPM using corrected formula
  float ppmCO2 = 116.6020682 * pow((resistance / RZERO_CLEAN_AIR), -2.769034857);
  //correctedPPMCO2
  float ppm = 116.6020682 * pow((resistance / correctedRZero), -2.769034857);

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
    
    delay(500);
    return;
  } else {
    if(isAutomatic){
      // Conditions that will happen regularly
      if(temperature < 20 && humidity <= 85 && round(ppm) <= 1000){
        digitalWrite(EXHAUST_PIN, HIGH);
        digitalWrite(HEATER_PIN, HIGH);
        digitalWrite(HUMIDIFIER_PIN, HIGH);
        digitalWrite(EXHAUST_PIN2, HIGH);
      } else if(temperature >= 20 && humidity <= 85 && ppm <= 1000){
        digitalWrite(HUMIDIFIER_PIN, HIGH);
        digitalWrite(EXHAUST_PIN2, HIGH);

        digitalWrite(EXHAUST_PIN, LOW);
        digitalWrite(HEATER_PIN, LOW);
      } else if(temperature < 20 && humidity > 85 && ppm <= 1000){
        digitalWrite(EXHAUST_PIN, HIGH);
        digitalWrite(HEATER_PIN, HIGH);

        digitalWrite(HUMIDIFIER_PIN, LOW);
        digitalWrite(EXHAUST_PIN2, LOW);
      } else if(temperature >= 20 && humidity > 85 && ppm <= 1000){
        digitalWrite(EXHAUST_PIN, HIGH);

        digitalWrite(HEATER_PIN, LOW);
        digitalWrite(HUMIDIFIER_PIN, LOW);
        digitalWrite(EXHAUST_PIN2, LOW);
      } 
      // Conditions that will rarely happen
      else if((temperature < 20 && humidity <= 85 && ppm > 1000) || (temperature < 20 && humidity > 85 && ppm > 1000)){
        digitalWrite(EXHAUST_PIN, HIGH);
        digitalWrite(HEATER_PIN, HIGH);

        digitalWrite(HUMIDIFIER_PIN, LOW);
        digitalWrite(EXHAUST_PIN2, LOW);
      } else if((temperature >= 20 && humidity <= 85 && ppm > 1000) || (temperature >= 20 && humidity > 85 && ppm > 1000)){
        digitalWrite(EXHAUST_PIN, HIGH);

        digitalWrite(HEATER_PIN, LOW);
        digitalWrite(HUMIDIFIER_PIN, LOW);
        digitalWrite(EXHAUST_PIN2, LOW);
      } 

      // Lvl 19 is the highest, Lvl 1 is the lowest
      if(waterLevel<=8){
        if(waterLevel==0){
          digitalWrite(WATER_PUMP_PIN, LOW);
        } else {
          digitalWrite(WATER_PUMP_PIN, HIGH);
        }
      } else if(waterLevel>=12){
        digitalWrite(WATER_PUMP_PIN, LOW);
      }

      // FOR PELTIER
      if(temperature < 20){
        digitalWrite(PELTIER_PIN, LOW);
        digitalWrite(HEATER_PIN, HIGH);
      } else {
        digitalWrite(PELTIER_PIN, HIGH);
        digitalWrite(HEATER_PIN, LOW);
      }
    }
  }

  delay(1000);

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
