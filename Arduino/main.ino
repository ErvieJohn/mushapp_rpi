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

// New
#define EXHAUST_PIN2 10

#define MQ135_PIN A0 // mq135
#define co2zero 55

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
  pinMode(EXHAUST_PIN2, OUTPUT);
  pinMode(WATER_PUMP_PIN, OUTPUT);
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

void loop(){
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

  // VALUES
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  humidity += -5.0;
  waterLevel = ultrasonic.ping_cm();

  // FOR MQ135
  int MQ135sensorValue = analogRead(MQ135_PIN); // Read analog value
  float resistance = getResistance(MQ135sensorValue); // Calculate resistance
  float ppm = getPPM(resistance); // Calculate CO2 concentration (ppm)

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
  } else {
    // Temperature
    if(temperature < 20) {
      /*
        Below 20C (mas malamig siya) so doon mag oopen si HEATER to 
        control the heat and MALAKING FAN para maglabas ng hangin or 
        lamig.
      */ 
      digitalWrite(EXHAUST_PIN, HIGH);
      digitalWrite(HEATER_PIN, HIGH);
    } else {
      /*
        In between 20-30 and 30 up, hindi mag oon ang HEATER and 
        MALAKING FAN. kasi nasa tamang range siya and if 30 UP, mainit 
        na siya, so OFF lang ang heater.
      */
      digitalWrite(EXHAUST_PIN, LOW);
      digitalWrite(HEATER_PIN, LOW);
    }

    // Humidifier
    if(humidity <= 85){
      /*
        - Below 70 (naka-on lang si HUMIDIFIER and MALIIT na FAN) 
          kasi siya yung nag bibigay ng fresh air inside proto and to 
          avoid dryness. if dry ang mushroom there is a chance na mag 
          fail yung pag develop niya.
        - In between 70 and 85% (STILL ON HUMIDIFIER AND MALIIT NA FAN) 
          to bring fresh air inside the proto 
      */
      digitalWrite(EXHAUST_PIN2, HIGH);
      digitalWrite(HUMIDIFIER_PIN, HIGH);
      digitalWrite(EXHAUST_PIN, LOW);
    } else {
      /*
        - 85 up, need i-off ang humidifier nad maliit na fan, it can 
          cause disease/bacteria sa mga mushrooms. if the range is too 
          high
        - if 85 up, need I-on naman ang malaking FAN para maglabas ng 
          hangin.
      */
      digitalWrite(EXHAUST_PIN2, LOW);
      digitalWrite(HUMIDIFIER_PIN, LOW);
      digitalWrite(EXHAUST_PIN, HIGH);
    }

    // CO2
    if(round(ppm) > 1000){
      /*
        - More than 1000ppm - it can cause drowsiness and poor air. 
          the mushroom  may be small or deformed. mushrooms may grow 
          more slowly or DIE.
        - if more than 1000pmm - need I-ON ang MALAKING FAN.
      */
      digitalWrite(EXHAUST_PIN, HIGH);
      digitalWrite(HUMIDIFIER_PIN, LOW);
      digitalWrite(EXHAUST_PIN2, LOW);
    } else {
      /*
      - to maintain the optimal level of CO2, HUMIDIFIER CAN HELP to regulate the CO2 levels. so need din siya iopen. (HUMIDIFIER AND FAN NA MALIIT)
      - Same factor sila if too high or low ang PPM ng CO2. mushrooms may grow more slowly or DIE and may be small or deformed.
      - Need i-on si HUMIDIFIER and MALIIT NA FAN if lower or in between the range
      */
      digitalWrite(EXHAUST_PIN, LOW);
      digitalWrite(HUMIDIFIER_PIN, HIGH);
      digitalWrite(EXHAUST_PIN2, HIGH);
    }

    // Waterpump
    // Lvl 13 is the lowest, Lvl 1 is the highest
    if(waterLevel>=5){
      digitalWrite(WATER_PUMP_PIN, HIGH);
    } else if(waterLevel<=2){
      digitalWrite(WATER_PUMP_PIN, LOW);
    }
  }

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
