#include "mqtt.h"
#include <iostream>
#include <cstring>

#define GREJAC_STANJE        "ploca1/grejac_vode/stanje"
#define GREJAC_TEMPERATURA   "ploca1/grejac_vode/temperatura"
#define GREJAC_BATERIJA      "ploca1/grejac_vode/baterija"


// Callback funkcija za povezivanje
void on_connect(struct mosquitto *mosq, void *obj, int reason_code) {
    std::cout << "Povezan sa MQTT brokerom, kod: " << reason_code << std::endl;
    if(reason_code == 0) {
        mosquitto_subscribe(mosq, NULL, GREJAC_STANJE, 0);
        mosquitto_subscribe(mosq, NULL, GREJAC_TEMPERATURA, 0);
        std::cout << "Pretplaćeno na teme: " << GREJAC_STANJE << ", " << GREJAC_TEMPERATURA << std::endl;
    }
    else {
        std::cerr << "Povezivanje nije uspelo, kod: " << reason_code << std::endl;
    }
}

// Callback funkcija za primanje poruka
void on_message(struct mosquitto *mosq, void *obj, const struct mosquitto_message *message) {
    if(!strcmp(message->topic, GREJAC_STANJE)) {
        if(message->payloadlen) {
            std::string payload((char*)message->payload, message->payloadlen);
            std::cout << "Primljena poruka na temi " << message->topic << ": " << payload << std::endl;
            parseStateMessage(payload);
            std::cout << "Grejac stanje: " << (currentActuatorData.aktivan ? "uključen" : "isključen") << std::endl;
            writeGrejacJsonToFile(currentActuatorData);
        } else {
            std::cout << "Primljena prazna poruka na temi " << message->topic << std::endl;
        }
    } else if (!strcmp(message->topic, GREJAC_TEMPERATURA)) {
        if(message->payloadlen) {
            std::string payload((char*)message->payload, message->payloadlen);
            std::cout << "Primljena poruka na temi " << message->topic << ": " << payload << std::endl;
            parseTemperatureMessage(payload);
            std::cout << "Grejac temperatura: " << currentActuatorData.temperatura << "°C" << std::endl;
            writeGrejacJsonToFile(currentActuatorData);
        } else {
            std::cout << "Primljena prazna poruka na temi " << message->topic << std::endl;
        }
        
    } else {
        std::cout << "Nepoznata tema: " << message->topic << std::endl;
    }
}

// Funkcija za slanje podataka na MQTT broker
void publishActuatorData(struct mosquitto* mosq, const ActuatorData& data) {
    char buffer[100];
    int rc;

    // Publish baterija
    snprintf(buffer, sizeof(buffer), "%d", data.baterija);
    rc = mosquitto_publish(mosq, NULL, GREJAC_BATERIJA, strlen(buffer), buffer, 0, false);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju podataka o bateriji: " << mosquitto_strerror(rc) << std::endl;
    }
}