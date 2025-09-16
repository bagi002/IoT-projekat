#include <iostream>
#include <mosquitto.h>
#include <string>
#include <cstdlib>
#include <cstring>
#include <unistd.h>
#include <fstream>
#include <thread>
#include <chrono>

#define MQTT_BROKER         "localhost"
#define MQTT_PORT           1883
#define MQTT_KEEPALIVE      60
#define MQTT_CLIENT_ID      "BetonSenzorClient"

#define BETON_TEMPERATURA  "ploca1/beton/temperatura"
#define BETON_VLAZNOST     "ploca1/beton/vlaznost"
#define SENZOR_GRESKA      "ploca1/beton/greska"
#define SENZOR_BATERIJA    "ploca1/beton/baterija"

#ifndef DEBUG
#define DEBUG 0
#endif

struct SensorData {
    double temperatura;
    double vlaznost;
    int baterija;
    bool hasGreska;
    std::string greska;
};

// Funckija za parsiranje jednostavnog JSON formata
SensorData parseJsonData(const std::string& jsonStr) {
    SensorData data = {};
    
    // Parsiranje temperature
    size_t tempPos = jsonStr.find("\"temperatura\":");
    if (tempPos != std::string::npos) {
        size_t start = jsonStr.find_first_of("0123456789.-", tempPos);
        size_t end = jsonStr.find_first_of(",}", start);
        if (start != std::string::npos && end != std::string::npos) {
            data.temperatura = std::stod(jsonStr.substr(start, end - start));
        }
    }
    
    // Parsiranje vlaznosti
    size_t vlazPos = jsonStr.find("\"vlaznost\":");
    if (vlazPos != std::string::npos) {
        size_t start = jsonStr.find_first_of("0123456789.-", vlazPos);
        size_t end = jsonStr.find_first_of(",}", start);
        if (start != std::string::npos && end != std::string::npos) {
            data.vlaznost = std::stod(jsonStr.substr(start, end - start));
        }
    }
    
    // Parsiranje baterije
    size_t batPos = jsonStr.find("\"baterija\":");
    if (batPos != std::string::npos) {
        size_t start = jsonStr.find_first_of("0123456789", batPos);
        size_t end = jsonStr.find_first_of(",}", start);
        if (start != std::string::npos && end != std::string::npos) {
            data.baterija = std::stoi(jsonStr.substr(start, end - start));
        }
    }
    
    // Parsiranje greske
    size_t greskaPos = jsonStr.find("\"greska\":");
    if (greskaPos != std::string::npos) {
        if (jsonStr.find("null", greskaPos) != std::string::npos) {
            data.hasGreska = false;
        } else {
            data.hasGreska = true;
            size_t start = jsonStr.find("\"", greskaPos + 8);
            size_t end = jsonStr.find("\"", start + 1);
            if (start != std::string::npos && end != std::string::npos) {
                data.greska = jsonStr.substr(start + 1, end - start - 1);
            }
        }
    }
    
    return data;
}

// Funkcija za slanje podataka na MQTT broker
void publishSensorData(struct mosquitto* mosq, const SensorData& data) {
    char buffer[100];
    int rc;

    // Publish temperatura
    snprintf(buffer, sizeof(buffer), "%.1f", data.temperatura);
    rc = mosquitto_publish(mosq, NULL, BETON_TEMPERATURA, strlen(buffer), buffer, 0, false);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju podataka o temperaturi: " << mosquitto_strerror(rc) << std::endl;
    }

    // Publish vlaznost
    snprintf(buffer, sizeof(buffer), "%.1f", data.vlaznost);
    rc = mosquitto_publish(mosq, NULL, BETON_VLAZNOST, strlen(buffer), buffer, 0, false);
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

// Funkcija za čitanje JSON podataka iz datoteke
std::string readJsonFromFile(const std::string& filename) {
    std::ifstream file(filename);
    std::string line;
    if (std::getline(file, line)) {
        return line;
    }
    return "";
}


int main() {

    struct mosquitto* mosq = NULL;
    int rc;
    
    std::cout << "Pokretanje MQTT klijenta za senzore betona..." << std::endl;

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
        std::string jsonData = readJsonFromFile("podaci.json");
        
        if (!jsonData.empty()) {
            // Parsiraj JSON podatke
            SensorData sensorData = parseJsonData(jsonData);
            
            // Debug flag
            if (DEBUG) {
                std::cout << "  Temperatura: " << sensorData.temperatura << "°C" << std::endl;
                std::cout << "  Vlaznost: " << sensorData.vlaznost << "%" << std::endl;
                std::cout << "  Baterija: " << sensorData.baterija << "%" << std::endl;
                if (sensorData.hasGreska) {
                    std::cout << "  Greska: " << sensorData.greska << std::endl;
                } else {
                    std::cout << "  Greska: nema" << std::endl;
                }
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

    // 7. Cistenje resursa i završetak
    mosquitto_loop_stop(mosq, true);
    mosquitto_disconnect(mosq);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();

    return 0;
}