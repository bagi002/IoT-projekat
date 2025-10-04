#ifndef MQTT_H
#define MQTT_H

#include <mosquitto.h>

// Deklaracije callback funkcija
void on_connect(struct mosquitto *mosq, void *obj, int reason_code);
void on_message(struct mosquitto *mosq, void *obj, const struct mosquitto_message *message);

#endif // MQTT_H