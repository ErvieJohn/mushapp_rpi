#include <MQ135.h>

#define PIN_MQ135 A0
MQ135 mq135_sensor(PIN_MQ135);

void setup() {
  Serial.begin(9600);
  Serial.println("MQ135 warming up...");
  delay(20000); // Warm-up time
}

void loop() {
  // Read raw analog value
  int rawValue = analogRead(PIN_MQ135);
  
  // Convert to voltage
  float voltage = rawValue * (5.0 / 1023.0);
  
  // Get PPM using the basic function
  float ppm = mq135_sensor.getPPM();
  
  // Get the current RZERO reading
  float rzero = mq135_sensor.getRZero();
  
  Serial.print("Raw Value: ");
  Serial.println(rawValue);
  Serial.print("Voltage: ");
  Serial.println(voltage);
  Serial.print("PPM: ");
  Serial.println(ppm);
  Serial.print("RZERO: ");
  Serial.println(rzero);
  Serial.println("------------------------");
  
  delay(2000);
}
