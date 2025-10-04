#ifndef MQTT_H
#define MQTT_H

#include <mosquitto.h>
#include "../Parse/parse.h"

// Deklaracije callback funkcija
void on_connect(struct mosquitto *mosq, void *obj, int reason_code);
void on_message(struct mosquitto *mosq, void *obj, const struct mosquitto_message *message);
void publishActuatorData(struct mosquitto* mosq, const ActuatorData& data);

#endif // MQTT_H
