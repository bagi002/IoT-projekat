#include "mqtt.h"
#include <iostream>
#include <cstring>
#include <mosquitto.h>

#define PUMPA_STANJE        "ploca1/vodena_pumpa/ventil/stanje"
#define PUMPA_VREME_RADA    "ploca1/vodena_pumpa/ventil/vreme_rada"
#define PUMPA_BATERIJA      "ploca1/vodena_pumpa/baterija"

// Eksterna promenljiva za stanje aktuatora
extern ActuatorData currentActuatorData;

// Callback funkcija za konekciju
void on_connect(struct mosquitto *mosq, void *obj, int reason_code) {
    std::cout << "Povezan sa MQTT brokerom, kod: " << reason_code << std::endl;
    if(reason_code == 0) {
        mosquitto_subscribe(mosq, NULL, PUMPA_STANJE, 0);
        mosquitto_subscribe(mosq, NULL, PUMPA_VREME_RADA, 0);
        std::cout << "Pretplaćeno na teme: " << PUMPA_STANJE << ", " << PUMPA_VREME_RADA << std::endl;
    }
    else {
        std::cerr << "Povezivanje nije uspelo, kod: " << reason_code << std::endl;
    }
}

// Callback funkcija za primanje poruka
void on_message(struct mosquitto *mosq, void *obj, const struct mosquitto_message *message) {
    if(!strcmp(message->topic, PUMPA_STANJE)) {
        if(message->payloadlen) {
            std::string payload((char*)message->payload, message->payloadlen);
            std::cout << "Primljena poruka na temi " << message->topic << ": " << payload << std::endl;
            parseStateMessage(payload);
            std::cout << "Pumpa stanje: " << (currentActuatorData.aktivan ? "uključena" : "isključena") << std::endl;
            writePumpJsonToFile(currentActuatorData);
        } else {
            std::cout << "Primljena prazna poruka na temi " << message->topic << std::endl;
        }
    } else if (!strcmp(message->topic, PUMPA_VREME_RADA)) {
        if(message->payloadlen) {
            std::string payload((char*)message->payload, message->payloadlen);
            std::cout << "Primljena poruka na temi " << message->topic << ": " << payload << std::endl;
            parseDurationMessage(payload);
            std::cout << "Pumpa vreme rada: " << currentActuatorData.vreme_rada << " min" << std::endl;
            writePumpJsonToFile(currentActuatorData);
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
    rc = mosquitto_publish(mosq, NULL, PUMPA_BATERIJA, strlen(buffer), buffer, 0, false);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju podataka o bateriji: " << mosquitto_strerror(rc) << std::endl;
    }
}
