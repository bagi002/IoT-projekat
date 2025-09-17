#include <iostream>
#include <mosquitto.h>
#include <thread>
#include <chrono>
#include <cstring>
#include "Parse/parse.h"
#include "MQTT/mqtt.h"

#define MQTT_BROKER          "localhost"
#define MQTT_PORT            1883
#define MQTT_KEEPALIVE       60
#define MQTT_CLIENT_ID       "GrejacVodeClient"

#ifndef DEBUG
#define DEBUG 1
#endif

// Globalna varijabla za čuvanje stanja aktuatora
ActuatorData currentActuatorData = {0, false, "", 0, 0.0};


int main() {

    struct mosquitto* mosq = NULL;
    int rc;

    // Inicijalizuj početne vrednosti u JSON fajlu
    writeGrejacJsonToFile(currentActuatorData);

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

    // Thread za periodično publishovanje poruka
    std::thread publish_thread([&mosq]() {

        while(true) {
             // 5. Čitanje podataka o bateriji iz BATERIJE.json
            int batteryLevel = readBatteryFromFile();
            
            if (batteryLevel > 0) {
                // Ažuriraj podatke o bateriji
                ActuatorData actuatorData = currentActuatorData;
                actuatorData.baterija = batteryLevel;

                // Debug flag
                if (DEBUG) {
                    std::cout << "  Baterija: " << actuatorData.baterija << "%" << std::endl;
                    if (actuatorData.hasGreska) {
                        std::cout << "  Greska: " << actuatorData.greska << std::endl;
                    } else {
                        std::cout << "  Greska: nema" << std::endl;
                    }
                    std::cout << "---" << std::endl;
                }   
            
                // 6. Slanje podataka na MQTT broker
                publishActuatorData(mosq, actuatorData);
            } 
            else {
                std::cout << "Nema podataka o bateriji u BATERIJE.json" << std::endl;
            }
            
            // Interval ocitavanja podataka
            std::this_thread::sleep_for(std::chrono::seconds(5));
        }   
    });

    if(publish_thread.joinable()) {
        publish_thread.join();
    }

    mosquitto_loop_stop(mosq, true);
    mosquitto_disconnect(mosq);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();

    if(DEBUG)
        std::cout << "Klijent je prekinuo vezu i očišćen je." << std::endl;

    return 0;
}