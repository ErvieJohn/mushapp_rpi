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
#define RELAY A5

#define anInput A0 // mq135
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

void setup()
{
  dht.begin(9600);
  Serial.begin(9600);
  pinMode(PELTIER_PIN, OUTPUT);
  pinMode(HUMIDIFIER_PIN, OUTPUT);
  pinMode(WATER_PUMP_PIN, OUTPUT);
  pinMode(EXHAUST_PIN, OUTPUT);

  pinMode(anInput,INPUT);
}

void loop()
{
  delay(2000);
  
  int co2raw = 0;
  int co2ppm = 0;
  int sum = 0;

  for (int x = 0;x<10;x++)  
  {                   
    sum+=analogRead(anInput);
    delay(200);
  }
  
  co2raw = sum/10;                          
  co2ppm = co2raw - co2zero; 

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity))
  {
    Serial.println("Failed to read data from sensor");
    delay(1000);
    return;
  }

  humidity += -5.0;
  waterLevel = ultrasonic.ping_cm();

  delay(1000);

//  Serial.print("Temperature: ");
//  Serial.print(temperature);
//  Serial.print("Humidity: ");
//  Serial.print(humidity);
//  Serial.print("Water Levell: ");
//  Serial.println(waterLevel);
//  Serial.print("LVL: ");
//
//  Serial.print("Peltier: ");
//  Serial.println((temperature > 30) ? "ON" : "OFF");
//
//  Serial.print("Humidifier: ");
//  Serial.println((humidity < 80) ? "ON" : "OFF");
//
//  Serial.print("Water Pump: ");
//  Serial.println((waterLevel <= 30) ? "ON" : (waterLevel >= 95) ? "OFF" : "N/A");

  StaticJsonDocument<200> jsonDoc;
  jsonDoc["temperature"] = temperature;
  jsonDoc["humidity"] = humidity;
  jsonDoc["waterLevel"] = waterLevel;
  jsonDoc["co2ppm"] = co2ppm;

  String jsonString;
  serializeJson(jsonDoc, jsonString);

  Serial.println("JSON data: " + jsonString);

  delay(1000);
}
