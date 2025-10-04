#include <iostream>
#include "MQTT/mqtt.h"

#define MQTT_BROKER         "localhost"
#define MQTT_PORT           1883
#define MQTT_KEEPALIVE      60
#define MQTT_CLIENT_ID      "KontrolerClient"

#ifndef DEBUG
#define DEBUG 1
#endif

int main() {
    struct mosquitto* mosq = NULL;
    int rc;

    // 1. Inicijalizacija biblioteke
    mosquitto_lib_init();

    // 2. Kreiranje novog Mosquitto klijenta
    mosq = mosquitto_new(MQTT_CLIENT_ID, true, NULL);
    if(!mosq) {
        std::cerr << "Neuspesno kreiranje Mosquitto klijenta: " << mosquitto_strerror(errno) << std::endl;
        mosquitto_lib_cleanup();
        return -1;
    }

    // 3. Podesavanje callback funkcija
    mosquitto_connect_callback_set(mosq, on_connect);
    mosquitto_message_callback_set(mosq, on_message);

    // 4. Povezivanje na MQTT broker
    rc = mosquitto_connect(mosq, MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE);
    if(rc) {
        std::cerr << "Neuspesno povezivanje na broker: " << mosquitto_strerror(rc) << std::endl;
        mosquitto_destroy(mosq);
        mosquitto_lib_cleanup();
        return -1;
    }

    // 5. Pokretanje petlje za obradu mrežnih događaja
    mosquitto_loop_start(mosq);
    std::cout << "Pritisni Enter za izlaz..." << std::endl;
    std::cin.get();
    mosquitto_loop_stop(mosq, true);

    // 6. Čišćenje resursa
    mosquitto_disconnect(mosq);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    
    return 0;
}