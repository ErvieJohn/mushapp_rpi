#include <NewPing.h>
#include <math.h>

#define ULTRASONIC_TRIGGER_PIN 5
#define ULTRASONIC_ECHO_PIN 6

NewPing ultrasonic(ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN);
int waterLevel;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);  
}

void loop() {
  // put your main code here, to run repeatedly:
  waterLevel = 20 - ultrasonic.ping_cm();
  Serial.println("Water Level: " + String(waterLevel));

  float waterPercent = ((float)waterLevel/19) * 100;
  Serial.println("Water Percentage: " + String(waterPercent) + "%");
  
  delay(1000);
}
