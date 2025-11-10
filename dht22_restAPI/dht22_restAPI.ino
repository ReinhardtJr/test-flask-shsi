#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "DHT.h"

const char *ssid = "WIFI-CHICKEN-CAGE";
const char *password = "shsikandang4321";

// REST API endpoint
const char *serverName = "http://192.168.0.13:5000/api/sensors";

#define DHT22_PIN 4 // Digital pin connected to DHT22 sensor
DHT dht22(DHT22_PIN, DHT22);

// Timing variables
unsigned long previousMillis = 0;
const unsigned long intervalSaveRequest = 60000; // 10 seconds

void saveSensorRecord(const char *sensor_id, DHT dht);

void setup()
{
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected! IP Address: ");
  Serial.println(WiFi.localIP());

  // Start DHT22
  dht22.begin();
}

void loop()
{
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= intervalSaveRequest)
  {
    previousMillis = currentMillis;

    if (WiFi.status() == WL_CONNECTED)
    {
      Serial.println("Saving sensor record...");
      saveSensorRecord("dht-garage", dht22);
    }
    else
    {
      Serial.println("WiFi Disconnected!");
    }
  }
}

void saveSensorRecord(const char *sensor_id, DHT dht)
{
  float humidity = dht.readHumidity();
  float tempC = dht.readTemperature();
  float tempF = dht.readTemperature(true);

  if (isnan(humidity) || isnan(tempC) || isnan(tempF))
  {
    Serial.println(F("Failed to read from DHT22 sensor!"));
    return;
  }

  float heatIndexF = dht.computeHeatIndex(tempF, humidity);
  float heatIndexC = dht.computeHeatIndex(tempC, humidity, false);

  WiFiClient client;
  HTTPClient http;
  http.begin(client, serverName);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<200> doc;
  doc["sensor_id"] = sensor_id;
  doc["temperature_in_c"] = tempC;
  doc["temperature_in_f"] = tempF;
  doc["humidity"] = humidity;
  doc["heat_index_in_c"] = heatIndexC;
  doc["heat_index_in_f"] = heatIndexF;

  String requestBody;
  serializeJson(doc, requestBody);

  int httpResponseCode = http.POST(requestBody);

  if (httpResponseCode > 0)
  {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    Serial.println(http.getString());
  }
  else
  {
    Serial.print("Error sending POST: ");
    Serial.println(httpResponseCode);
  }

  http.end();
}
