#ifndef MQTT_H
#define MQTT_H

#include <mosquitto.h>
#include "../Parse/parse.h"

void publishSensorData(struct mosquitto* mosq, const SensorData& data);

#endif // MQTT_H
