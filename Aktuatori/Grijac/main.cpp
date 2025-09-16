#include <iostream>
#include <mosquitto.h>
#include <fstream>
#include <thread>
#include <chrono>
#include <cstring>

#define MQTT_BROKER          "localhost"
#define MQTT_PORT            1883
#define MQTT_KEEPALIVE       60
#define MQTT_CLIENT_ID       "GrejacVodeClient"

#define GREJAC_STATE         "ploca1/grejac_vode/state"
#define GREJAC_TEMPERATURA   "ploca1/grejac_vode/temperatura"
#define GREJAC_BATERIJA      "ploca1/grejac_vode/baterija"
#define GREJAC_GRESKA        "ploca1/grejac_vode/greska"

#ifndef DEBUG
#define DEBUG 1
#endif

struct ActuatorData {
    int baterija;
    bool hasGreska;
    std::string greska;
    bool aktivan;
    int temperatura;
};

// Globalna varijabla za čuvanje stanja aktuatora
ActuatorData currentActuatorData = {0, false, "", false, 0};

// Funckija za parsiranje jednostavnog JSON formata
ActuatorData parseJsonData(const std::string& jsonStr) {
    ActuatorData data = currentActuatorData; // Kopiraj trenutno stanje


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

// Funkcija za parsiranje state poruke od kontrolera
void parseStateMessage(const std::string& message) {
    if (message == "true") {
        currentActuatorData.aktivan = true;
    } else if (message == "false") {
        currentActuatorData.aktivan = false;
    }
}

// Funkcija za parsiranje temperature poruke od kontrolera
void parseTemperatureMessage(const std::string& message) {
    try {
        currentActuatorData.temperatura = std::stoi(message);
    } catch (const std::exception& e) {
        std::cerr << "Greška pri parsiranju temperature: " << e.what() << std::endl;
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

// Funkcija za kreiranje i pisanje JSON datoteke sa stanjem grejača
void writeGrejacJsonToFile(const ActuatorData& data, const std::string& filename = "grejac.json") {
    std::ofstream file(filename);
    if (file.is_open()) {
        file << "{\"aktivan\": " << (data.aktivan ? "true" : "false") 
             << ", \"temperatura\": " << data.temperatura << "}";
        file.close();
        if (DEBUG) {
            std::cout << "Stanje grejača zapisano u " << filename << std::endl;
        }
    } else {
        std::cerr << "Greška pri pisanju u datoteku " << filename << std::endl;
    }
}

// Callback funkcija za povezivanje
void on_connect(struct mosquitto *mosq, void *obj, int reason_code) {
    std::cout << "Povezan sa MQTT brokerom, kod: " << reason_code << std::endl;
    if(reason_code == 0) {
        mosquitto_subscribe(mosq, NULL, GREJAC_STATE, 0);
        mosquitto_subscribe(mosq, NULL, GREJAC_TEMPERATURA, 0);
        std::cout << "Pretplaćeno na teme: " << GREJAC_STATE << ", " << GREJAC_TEMPERATURA << std::endl;
    }
}

// Callback funkcija za primanje poruka
void on_message(struct mosquitto *mosq, void *obj, const struct mosquitto_message *message) {
    if(!strcmp(message->topic, GREJAC_STATE)) {
        if(message->payloadlen) {
            std::string payload((char*)message->payload, message->payloadlen);
            std::cout << "Primljena poruka na temi " << message->topic << ": " << payload << std::endl;
            parseStateMessage(payload);
            std::cout << "Grejac stanje: " << (currentActuatorData.aktivan ? "uključen" : "isključen") << std::endl;
        } else {
            std::cout << "Primljena prazna poruka na temi " << message->topic << std::endl;
        }
    } else if (!strcmp(message->topic, GREJAC_TEMPERATURA)) {
        if(message->payloadlen) {
            std::string payload((char*)message->payload, message->payloadlen);
            std::cout << "Primljena poruka na temi " << message->topic << ": " << payload << std::endl;
            parseTemperatureMessage(payload);
            std::cout << "Grejac temperatura: " << currentActuatorData.temperatura << "°C" << std::endl;
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

    // Publish greska ako postoji
    if (data.hasGreska) {
        rc = mosquitto_publish(mosq, NULL, GREJAC_GRESKA, data.greska.length(), data.greska.c_str(), 0, false);
        if (rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "Greška pri slanju podataka o grešci: " << mosquitto_strerror(rc) << std::endl;
        }
    }
}

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

    // Thread za periodično publishovanje poruka
    std::thread publish_thread([&mosq]() {
        int message_count = 0;
        int rc;

        while(true) {
             // 5. Čitanje JSON podataka iz datoteke
            std::string jsonData = readJsonFromFile("podaci.json");
            
            if (!jsonData.empty()) {
                // Parsiraj JSON podatke
                ActuatorData actuatorData = parseJsonData(jsonData);

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
                std::cout << "Nema podataka u datoteci podaci.json" << std::endl;
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