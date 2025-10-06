#include <iostream>
#include "MQTT/SystemController.h"
#include <thread>
#include <chrono>

#define MQTT_PORT           1883
#define MQTT_KEEPALIVE      60
#define MQTT_CLIENT_ID      "KontrolerClient"

#ifndef DEBUG
#define DEBUG 1
#endif

int main() {
    SystemController controller;
    
    // Učitaj simulirano vreme pre povezivanja
    std::string time_config_path = "/home/radov1c/Desktop/FTN/Letnji/IoT/IoT-projekat/simulacija/SimData/time.json";
    if(!controller.loadTimeConfig(time_config_path)) {
        std::cerr << "Upozorenje: Nije moguće učitati time.json. Koristi se sistemsko vreme." << std::endl;
    } else {
        std::cout << "Učitan time.json fajl sa putanje: " << time_config_path << std::endl;
    }
    
    if(!controller.connect("localhost", MQTT_PORT, MQTT_KEEPALIVE)) {
        std::cerr << "Neuspešno povezivanje na MQTT broker." << std::endl;
        return 1;
    }

    std::cout << "Sistem kontroler pokrenut. Pritisnite Ctrl+C za zaustavljanje." << std::endl;
    
    // Sačekaj malo da stigne inicijalna poruka sa senzora
    std::this_thread::sleep_for(std::chrono::seconds(2));

    // Glavna kontrolna petlja
    while(controller.isConnected()) {
        // Ažuriraj simulirano vreme (učitaj najnovije vrednosti iz time.json)
        controller.updateSimulatedTime();
        
        // Pozovi kontrolni sistem koji analizira stanje i upravlja aktuatorima
        controller.controlSystem();
        
        // Prikaži status sistema
        controller.printStatus();
        
        // Prikaži alarme
        controller.printAlarms();
        
        // Pauza između iteracija (npr. 2 sekundi)
        std::this_thread::sleep_for(std::chrono::seconds(2));
    }

    std::cout << "Kontroler se isključuje..." << std::endl;
    controller.disconnect();

    return 0;
}