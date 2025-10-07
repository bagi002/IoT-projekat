#include <iostream>
#include <mosquitto.h>
#include <string>
#include <cstdlib>
#include <cstring>
#include <unistd.h>
#include <fstream>
#include <thread>
#include <chrono>
#include "Parse/parse.h"
#include "MQTT/mqtt.h"

#define MQTT_BROKER         "localhost"
#define MQTT_PORT           1883
#define MQTT_KEEPALIVE      60
#define MQTT_CLIENT_ID      "VazduhSenzorClient"

#ifndef DEBUG
#define DEBUG 1
#endif

int main() {

    struct mosquitto* mosq = NULL;
    int rc;
    
    std::cout << "Pokretanje MQTT klijenta za senzore vazduha..." << std::endl;

    // 1. Inicijalizacija MQTT klijenta
    mosquitto_lib_init();

    // 2. Kreiranje novog MQTT klijenta
    mosq = mosquitto_new(MQTT_CLIENT_ID, true, NULL);
    if (!mosq) {
        std::cerr << "Greška pri kreiranju MQTT klijenta." << std::endl;
        return 1;
    }
    
    // 3. Povezivanje na MQTT broker
    rc = mosquitto_connect(mosq, MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri povezivanju na MQTT broker: " << mosquitto_strerror(rc) << std::endl;
        mosquitto_destroy(mosq);
        return 1;
    }

    // 4. Pokretanje petlje za obradu poruka
    rc = mosquitto_loop_start(mosq);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri pokretanju petlje: " << mosquitto_strerror(rc) << std::endl;
        mosquitto_disconnect(mosq);
        mosquitto_destroy(mosq);
        return 1;
    }

    
    while (true) {
        // 5. Čitanje JSON podataka iz datoteke
        std::string jsonData = readJsonFromFile("/home/radov1c/Desktop/FTN/Letnji/IoT/IoT-projekat/simulacija/SimData/VAZDUH.JSON");
        
        if (!jsonData.empty()) {
            // Parsiraj JSON podatke
            SensorData sensorData = parseJsonData(jsonData);
            
            // Provera baterije - ako je 0%, prestani sa radom
            if (sensorData.baterija <= 0) {
                std::cout << "\n[KRITIČNO] Baterija senzora vazduha je prazna (0%)!" << std::endl;
                std::cout << "Senzor se isključuje..." << std::endl;
                
                // Pošalji poslednji status sa baterijom 0%
                publishSensorData(mosq, sensorData);
                
                // Zaustavi rad
                break;
            }
            
            // Debug flag
            if (DEBUG) {
                std::cout << "  Temperatura: " << sensorData.temperatura << "°C" << std::endl;
                std::cout << "  Vlaznost: " << sensorData.vlaznost << "%" << std::endl;
                std::cout << "  Baterija: " << sensorData.baterija << "%" << std::endl;
                std::cout << "---" << std::endl;
            }   
           
            // 6. Slanje podataka na MQTT broker
            publishSensorData(mosq, sensorData);
        } 
        else {
            std::cout << "Nema podataka u datoteci podaci.json" << std::endl;
        }
        
        // Interval ocitavanja podataka
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
    
    std::cout << "Senzor vazduha potpuno isključen zbog prazne baterije." << std::endl;

    // 7. Cistenje resursa i završetak
    mosquitto_loop_stop(mosq, true);
    mosquitto_disconnect(mosq);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();

    return 0;
}