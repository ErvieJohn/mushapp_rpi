#include <MQ135.h>
#include <DHT.h>

#define PIN_MQ135 A1  // MQ135 Analog Input Pin
#define DHTPIN 2       // DHT Digital Input Pin
#define DHTTYPE DHT11  // DHT11 or DHT22

MQ135 mq135_sensor(PIN_MQ135);
DHT dht(DHTPIN, DHTTYPE);

// Define constants for CO2 calculation
#define RL 10.0  // Load resistance in kΩ (check your setup, usually 1kΩ or 10kΩ)
#define RZERO_CLEAN_AIR 1140.0  // Adjust based on your calibration

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Validate DHT sensor readings
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    return;
  }

  // Read resistance and calculate new RZero
  float resistance = mq135_sensor.getResistance();
  float rzero = resistance / exp((log10(400.0) - 1.78) / -2.93);  // Using CO2 calibration formula
  float correctedRZero = mq135_sensor.getCorrectedRZero(temperature, humidity);

  // Calculate CO2 PPM using corrected formula
  float ppmCO2 = 116.6020682 * pow((resistance / RZERO_CLEAN_AIR), -2.769034857);
  float correctedPPMCO2 = 116.6020682 * pow((resistance / correctedRZero), -2.769034857);

  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.print("°C, Humidity: ");
  Serial.print(humidity);
  Serial.print("%, MQ135 RZero: ");
  Serial.print(rzero);
  Serial.print("\t Corrected RZero: ");
  Serial.print(correctedRZero);
  Serial.print("\t Resistance: ");
  Serial.print(resistance);
  Serial.print("\t CO2 PPM: ");
  Serial.print(ppmCO2);
  Serial.print("ppm");
  Serial.print("\t Corrected CO2 PPM: ");
  Serial.print(correctedPPMCO2);
  Serial.println("ppm");

  delay(3000);
}
