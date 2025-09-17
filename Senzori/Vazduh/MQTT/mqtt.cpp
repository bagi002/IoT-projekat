#include "mqtt.h"
#include <iostream>
#include <cstring>

#define VAZDUH_TEMPERATURA "ploca1/povrsina/temperatura"
#define VAZDUH_VLAZNOST    "ploca1/povrsina/vlaznost"
#define SENZOR_GRESKA      "ploca1/povrsina/greska"
#define SENZOR_BATERIJA    "ploca1/povrsina/baterija"

// Funkcija za slanje podataka na MQTT broker
void publishSensorData(struct mosquitto* mosq, const SensorData& data) {
    char buffer[100];
    int rc;

    // Publish temperatura
    snprintf(buffer, sizeof(buffer), "%.1f", data.temperatura);
    rc = mosquitto_publish(mosq, NULL, VAZDUH_TEMPERATURA, strlen(buffer), buffer, 0, false);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju podataka o temperaturi: " << mosquitto_strerror(rc) << std::endl;
    }

    // Publish vlaznost
    snprintf(buffer, sizeof(buffer), "%.1f", data.vlaznost);
    rc = mosquitto_publish(mosq, NULL, VAZDUH_VLAZNOST, strlen(buffer), buffer, 0, false);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju podataka o vlaznosti: " << mosquitto_strerror(rc) << std::endl;
    }

    // Publish baterija
    snprintf(buffer, sizeof(buffer), "%d", data.baterija);
    rc = mosquitto_publish(mosq, NULL, SENZOR_BATERIJA, strlen(buffer), buffer, 0, false);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju podataka o bateriji: " << mosquitto_strerror(rc) << std::endl;
    }

    // Publish greska ako postoji
    if (data.hasGreska) {
        rc = mosquitto_publish(mosq, NULL, SENZOR_GRESKA, data.greska.length(), data.greska.c_str(), 0, false);
        if (rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "Greška pri slanju podataka o grešci: " << mosquitto_strerror(rc) << std::endl;
        }
    }
}
