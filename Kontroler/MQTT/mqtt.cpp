#include "mqtt.h"
#include <iostream>

#define BETON_TEMPERATURA  "ploca1/beton/temperatura"
#define BETON_VLAZNOST     "ploca1/beton/vlaznost"
#define BETON_GRESKA       "ploca1/beton/greska"
#define BETON_BATERIJA     "ploca1/beton/baterija"
#define VAZDUH_TEMPERATURA "ploca1/povrsina/temperatura"
#define VAZDUH_VLAZNOST    "ploca1/povrsina/vlaznost"
#define VAZDUH_GRESKA      "ploca1/povrsina/greska"
#define VAZDUH_BATERIJA    "ploca1/povrsina/baterija"

#define PUMPA_STANJE      "ploca1/vodena_pumpa/ventil/stanje"
#define PUMPA_VREME_RADA "ploca1/vodena_pumpa/ventil/vreme_rada"
#define PUMPA_GRESKA     "ploca1/vodena_pumpa/ventil/greska"
#define PUMPA_BATERIJA   "ploca1/vodena_pumpa/ventil/baterija"

#define GREJAC_STANJE        "ploca1/grejac_vode/stanje"
#define GREJAC_TEMPERATURA   "ploca1/grejac_vode/temperatura"
#define GREJAC_BATERIJA      "ploca1/grejac_vode/baterija"
#define GREJAC_GRESKA        "ploca1/grejac_vode/greska"

// Callback funkcija za povezivanje
void on_connect(struct mosquitto *mosq, void *obj, int reason_code) {
    std::cout << "Povezan sa MQTT brokerom, kod: " << reason_code << std::endl;
    if(reason_code == 0) {
        mosquitto_subscribe(mosq, NULL, BETON_TEMPERATURA, 0);
        mosquitto_subscribe(mosq, NULL, BETON_VLAZNOST, 0);
        mosquitto_subscribe(mosq, NULL, BETON_GRESKA, 0);
        mosquitto_subscribe(mosq, NULL, BETON_BATERIJA, 0);
        mosquitto_subscribe(mosq, NULL, VAZDUH_TEMPERATURA, 0);
        mosquitto_subscribe(mosq, NULL, VAZDUH_VLAZNOST, 0);
        mosquitto_subscribe(mosq, NULL, VAZDUH_GRESKA, 0);
        mosquitto_subscribe(mosq, NULL, VAZDUH_BATERIJA, 0);
        mosquitto_subscribe(mosq, NULL, PUMPA_GRESKA, 0);
        mosquitto_subscribe(mosq, NULL, PUMPA_BATERIJA, 0);
        mosquitto_subscribe(mosq, NULL, GREJAC_GRESKA, 0);
        mosquitto_subscribe(mosq, NULL, GREJAC_BATERIJA, 0);
        std::cout << "Pretplaćeno na teme senzora i aktuatora." << std::endl;
    } else {
        std::cerr << "Povezivanje nije uspelo, kod: " << reason_code << std::endl;
    }
}