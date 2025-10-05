#include "SystemController.h"


#ifndef DEBUG
#define DEBUG 1
#endif

SystemController::SystemController() : mosq(nullptr) {
    mosquitto_lib_init();
}

SystemController::~SystemController() {
    disconnect();
    mosquitto_lib_cleanup();
}

bool SystemController::connect(const std::string& broker, int port, int keepalive) {
    // std::lock_guard<std::mutex> lock(mutex);
    if(mosq) {
        std::cerr << "Već ste povezani na MQTT broker." << std::endl;
        return false;
    }

    mosq = mosquitto_new("SystemControllerClient", true, this);
    if(!mosq) {
        std::cerr << "Neuspesno kreiranje Mosquitto klijenta: " << mosquitto_strerror(errno) << std::endl;
        return false;
    }

    mosquitto_connect_callback_set(mosq, SystemController::onConnect);
    mosquitto_message_callback_set(mosq, SystemController::onMessage);

    int rc = mosquitto_connect(mosq, broker.c_str(), port, keepalive);
    if(rc) {
        std::cerr << "Neuspesno povezivanje na broker: " << mosquitto_strerror(rc) << std::endl;
        mosquitto_destroy(mosq);
        mosq = nullptr;
        return false;
    }

    rc = mosquitto_loop_start(mosq);
    if(rc) {
        std::cerr << "Neuspesno pokretanje petlje: " << mosquitto_strerror(rc) << std::endl;
        mosquitto_disconnect(mosq);
        mosquitto_destroy(mosq);
        mosq = nullptr;
        return false;
    }

    return true;
}

void SystemController::disconnect() {
    if(mosq) {
        mosquitto_loop_stop(mosq, true);
        mosquitto_disconnect(mosq);
        mosquitto_destroy(mosq);
        mosq = nullptr;
    }
}

bool SystemController::isConnected() const {
    return mosq != nullptr;
}

// Static callback - koristi userdata da dobije pointer na instancu klase
void SystemController::onConnect(struct mosquitto* mosq, void* obj, int result) {
    SystemController* controller = static_cast<SystemController*>(obj);
    
    if (result == 0) {
        std::cout << "Kontroler povezan na MQTT broker" << std::endl;
        
        // Subscribe na sve topike
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

        mosquitto_subscribe(mosq, NULL, GREJAC_BATERIJA, 0);
        mosquitto_subscribe(mosq, NULL, GREJAC_GRESKA, 0);

        std::cout << "Pretplacen na sve topike" << std::endl;
    } else {
        std::cerr << "Greška pri povezivanju: " << result << std::endl;
    }
}

void SystemController::onMessage(struct mosquitto* mosq, void* obj, const struct mosquitto_message* message) {
    SystemController* controller = static_cast<SystemController*>(obj);
    
    if (message->payloadlen) {
        std::string topic(message->topic);
        std::string payload((char*)message->payload, message->payloadlen);
        
        if (!DEBUG) {
            std::cout << "Topic: " << topic << " | Payload: " << payload << std::endl;
        }
        
        // Parsiranje i ažuriranje podataka
        try {
            if (topic == BETON_TEMPERATURA) {
                float temp = std::stof(payload);
                controller->betonSensor.temperature = temp;
                controller->betonSensor.timestamp = controller->getCurrentTimestamp();
            }
            else if (topic == BETON_VLAZNOST) {
                float hum = std::stof(payload);
                controller->betonSensor.humidity = hum;
            }
            else if (topic == BETON_GRESKA) {
                controller->betonSensor.error = payload;
            }
            else if (topic == BETON_BATERIJA) {
                int bat = std::stoi(payload);
                controller->betonSensor.battery = bat;
            }
            // Vazduh senzor
            else if (topic == VAZDUH_TEMPERATURA) {
                controller->airSensor.temperature = std::stof(payload);
                controller->airSensor.timestamp = controller->getCurrentTimestamp();
            }
            else if (topic == VAZDUH_VLAZNOST) {
                controller->airSensor.humidity = std::stof(payload);
            }
            else if (topic == VAZDUH_GRESKA) {
                controller->airSensor.error = payload;
            }
            else if (topic == VAZDUH_BATERIJA) {
                controller->airSensor.battery = std::stoi(payload);
            }
            // Pumpa
            else if (topic == PUMPA_BATERIJA) {
                controller->pump.battery = std::stoi(payload);
                controller->pump.timestamp = controller->getCurrentTimestamp();
            }
            else if (topic == PUMPA_GRESKA) {
                controller->pump.error = payload;
            }
            // Grejac
            else if (topic == GREJAC_BATERIJA) {
                controller->heater.battery = std::stoi(payload);
            }
            else if (topic == GREJAC_GRESKA) {
                controller->heater.error = payload;
            }
            else {
                std::cerr << "Nepoznat topic: " << topic << std::endl;
            }
        } catch (const std::exception& e) {
            std::cerr << "Greška pri parsiranju: " << e.what() << std::endl;
        }
    }
}

bool SystemController::setPumpState(int active, int duration) {
    if(!mosq) {
        std::cerr << "Niste povezani na MQTT broker." << std::endl;
        return false;
    }
    // std::lock_guard<std::mutex> lock(mutex);

    // Slanje stanja pumpe
    std::string state_str = std::to_string(active);

    // Vreme rada pumpe
    std::string duration_str = std::to_string(duration);


    int rc = mosquitto_publish(mosq, NULL, PUMPA_STATUS, state_str.size(), state_str.c_str(), 0, false);
    if(rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju stanja pumpe: " << mosquitto_strerror(rc) << std::endl;
        return false;
    }

    // Ako je pumpa aktivirana, salje se i vreme rada
    if(active && duration > 0) {
        rc = mosquitto_publish(mosq, NULL, PUMPA_VREME_RADA, duration_str.size(), duration_str.c_str(), 0, false);
        if(rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "Greška pri slanju vremena rada pumpe: " << mosquitto_strerror(rc) << std::endl;
            return false;
        }
        pump.remaining_time = std::stoll(duration_str);
    } else {
        rc = mosquitto_publish(mosq, NULL, PUMPA_VREME_RADA, duration_str.size(), duration_str.c_str(), 0, false);
        if(rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "Greška pri slanju vremena rada pumpe: " << mosquitto_strerror(rc) << std::endl;
            return false;
        }
   }
    pump.active = active;

    if(DEBUG) {
        std:: cout << "Poslata komanda pumpi: " << active << (duration > 0 ? (" na " + std::to_string(duration) + "s") : "") << std::endl;
    }

    return true;
}

bool SystemController::setHeaterState(int active, double target_temp) {
    if(!mosq) {
        std::cerr << "Niste povezani na MQTT broker." << std::endl;
        return false;
    }
    // std::lock_guard<std::mutex> lock(mutex);

    std::string state_str = std::to_string(active);
    std::string temp_str = std::to_string(target_temp);

    int rc = mosquitto_publish(mosq, NULL, GREJAC_STATUS, state_str.size(), state_str.c_str(), 0, false);
    heater.active = active;
    if(rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju stanja grejača: " << mosquitto_strerror(rc) << std::endl;
        return false;
    }

    if(active) {
        rc = mosquitto_publish(mosq, NULL, GREJAC_TARGET_TEMP, temp_str.size(), temp_str.c_str(), 0, false);
        heater.temperature = target_temp;
        if(rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "Greška pri slanju ciljne temperature: " << mosquitto_strerror(rc) << std::endl;
            return false;
        }
    } else {
        temp_str = "0";
        rc = mosquitto_publish(mosq, NULL, GREJAC_TARGET_TEMP, temp_str.size(), temp_str.c_str(), 0, false);
        heater.temperature = 0.0;
        if(rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "Greška pri slanju ciljne temperature: " << mosquitto_strerror(rc) << std::endl;
            return false;
        }
        heater.temperature = 0.0;
    }
    
    if(DEBUG) {
        std:: cout << "Poslata komanda grejaču: " << active << (active ? (" na " + std::to_string(target_temp) + "°C") : "") << std::endl;
    }

    return true;
}

// Pomoćna metoda za dobijanje trenutnog timestamp-a u milisekundama
long long SystemController::getCurrentTimestamp() const {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
}

long long SystemController::getConcreteAgeHours() const {
    if (timeConfig.pour_timestamp == 0) {
        return 0;
    }
    return (getCurrentTimestamp() - timeConfig.pour_timestamp) / (1000 * 3600);
}

float SystemController::getTargetTempDifference() const {
    long long age = getConcreteAgeHours();
    if (age <= 12) return 3.0f;
    if (age <= 24) return 5.0f;
    if (age <= 168) return 7.0f; // 1 - 7 dana
    return 7.0f;
}

float SystemController::getTargetHumidity() const {
    long long age = getConcreteAgeHours();
    if (age <= 12) return 80.0f;
    if (age <= 24) return 60.0f;
    if (age <= 48) return 50.0f;
    if (age <= 72) return 40.0f;
    if (age <= 168) return 15.0f; // 3 - 7 dana
    return 15.0f;
}

void SystemController::addAlarm(AlarmLevel level, const std::string& message) {
    Alarm alarm;
    alarm.level = level;
    alarm.message = message;
    alarm.timestamp = getCurrentTimestamp();
    
    alarms.push_back(alarm);
    
    std::string levelStr;
    switch(level) {
        case AlarmLevel::INFO: 
            levelStr = "INFO"; 
            break;
        case AlarmLevel::WARNING: 
            levelStr = "WARNING"; 
            break;
        case AlarmLevel::CRITICAL: 
            levelStr = "CRITICAL"; 
            break;
        default: 
            levelStr = "UNKNOWN"; 
            break;
    }
    
    std::cout << "[" << levelStr << "] " << message << std::endl;
}

void SystemController::checkAlarms() {
    // Kritične temperature
    if (betonSensor.temperature < CRITICAL_MIN_TEMP) {
        addAlarm(AlarmLevel::CRITICAL, "Temperatura betona ispod kritične (< 0°C): " + 
                 std::to_string(betonSensor.temperature) + "°C");
    }
    if (betonSensor.temperature > CRITICAL_MAX_TEMP) {
        addAlarm(AlarmLevel::CRITICAL, "Temperatura betona iznad kritične (> 40°C): " + 
                 std::to_string(betonSensor.temperature) + "°C");
    }
    
    // Temperaturna razlika
    float tempDiff = std::abs(betonSensor.temperature - airSensor.temperature);
    float maxDiff = getTargetTempDifference();
    if (tempDiff > maxDiff) {
        addAlarm(AlarmLevel::WARNING, "Razlika temperatura (" + std::to_string(tempDiff) + 
                 "°C) prelazi dozvoljenu (" + std::to_string(maxDiff) + "°C)");
    }
    
    // Vlažnost
    float targetHumidity = getTargetHumidity();
    if (betonSensor.humidity < targetHumidity) {
        addAlarm(AlarmLevel::WARNING, "Vlažnost betona (" + std::to_string(betonSensor.humidity) + 
                 "%) ispod ciljne (" + std::to_string(targetHumidity) + "%)");
    }
    
    // Niska baterija
    if (betonSensor.battery < LOW_BATTERY_THRESHOLD) {
        addAlarm(AlarmLevel::INFO, "Niska baterija senzora betona: " + 
                 std::to_string(betonSensor.battery) + "%");
    }
    if (airSensor.battery < LOW_BATTERY_THRESHOLD) {
        addAlarm(AlarmLevel::INFO, "Niska baterija senzora vazduha: " + 
                 std::to_string(airSensor.battery) + "%");
    }
    if (pump.battery < LOW_BATTERY_THRESHOLD) {
        addAlarm(AlarmLevel::INFO, "Niska baterija pumpe: " + 
                 std::to_string(pump.battery) + "%");
    }
    if (heater.battery < LOW_BATTERY_THRESHOLD) {
        addAlarm(AlarmLevel::INFO, "Niska baterija grijača: " + 
                 std::to_string(heater.battery) + "%");
    }
}

bool SystemController::canActivatePump() const {
    // Provera temperature vazduha
    if (airSensor.temperature < MIN_AIR_TEMP_FOR_PUMP) {
        return false;
    }
    
    // Provera pauze između aktivacija
    if (pump.last_deactivation > 0) {
        long long timeSinceDeactivation = (getCurrentTimestamp() - pump.last_deactivation) / 1000;
        if (timeSinceDeactivation < MIN_PUMP_PAUSE) {
            return false;
        }
    }
    
    // Provera maksimalnog trajanja
    if (pump.active) {
        long long activeDuration = (getCurrentTimestamp() - pump.last_activation) / 1000;
        if (activeDuration >= MAX_PUMP_DURATION) {
            return false;
        }
    }
    
    return true;
}

void SystemController::controlSystem() {
    // std::lock_guard<std::mutex> lock(mutex);
    
    checkAlarms();
    
    float targetHumidity = getTargetHumidity();
    bool needsWater = betonSensor.humidity < targetHumidity;
    bool needsCooling = betonSensor.temperature > MAX_CONCRETE_TEMP;
    bool needsHeating = betonSensor.temperature < MIN_CONCRETE_TEMP;
    bool airTooHot = airSensor.temperature > MIN_AIR_TEMP_FOR_HEATING && needsWater;
    
    // Kontrola grijača
    if (needsHeating || (airSensor.temperature < MIN_AIR_TEMP_FOR_HEATING && needsWater)) {
        if (heater.active == HEATER_STATE_OFF) {
            double targetTemp = needsHeating ? MIN_CONCRETE_TEMP + 5.0 : 25.0;
            setHeaterState(HEATER_STATE_ON, targetTemp);
        }
    } else {
        if (heater.active == HEATER_STATE_ON) {
            setHeaterState(HEATER_STATE_OFF);
        }
    }
    
    // Kontrola pumpe
    if ((needsWater || needsCooling) && canActivatePump()) {
        if (pump.active == PUMP_STATE_OFF) {
            int duration = 300; // 5 minuta početno
            if (betonSensor.humidity < targetHumidity - 20) {
                duration = 600; // 10 minuta za veliku razliku
            }
            setPumpState(PUMP_STATE_ON, duration);
            pump.last_activation = getCurrentTimestamp();
        }
    } else if (pump.active == PUMP_STATE_ON) {
        long long activeDuration = (getCurrentTimestamp() - pump.last_activation) / 1000;
        if (activeDuration >= MAX_PUMP_DURATION || !needsWater) {
            setPumpState(PUMP_STATE_OFF, 0);
            pump.last_deactivation = getCurrentTimestamp();
        }
    }
}

// bool SystemController::loadTimeConfig(const std::string& filepath) {
//     try {
//         std::ifstream file(filepath);
//         if (!file.is_open()) {
//             std::cerr << "Nije moguće otvoriti fajl: " << filepath << std::endl;
//             return false;
//         }
        
//         json j;
//         file >> j;
        
//         timeConfig.date = j["date"];
//         timeConfig.time = j["time"];
//         timeConfig.step_minutes = j["step_minutes"];
        
//         // Postavi pour_timestamp na trenutno vrijeme (simulacija)
//         timeConfig.pour_timestamp = getCurrentTimestamp();
        
//         std::cout << "Učitana konfiguracija vremena: " << timeConfig.date 
//                   << " " << timeConfig.time << std::endl;
//         return true;
//     } catch (const std::exception& e) {
//         std::cerr << "Greška pri čitanju JSON fajla: " << e.what() << std::endl;
//         return false;
//     }
// }

// void SystemController::simulateTimeStep() {
//     // Ova metoda će u budućnosti simulirati protok vremena
//     // Za sada samo poziva kontrolni sistem
//     controlSystem();
// }

// void SystemController::runControlLoop() {
//     while (isConnected()) {
//         simulateTimeStep();
//         std::this_thread::sleep_for(std::chrono::seconds(timeConfig.step_minutes * 60));
//     }
// }

void SystemController::printStatus() const {
    std::cout << "\n===== STATUS SISTEMA =====" << std::endl;
    std::cout << "Starost betona: " << getConcreteAgeHours() << " sati" << std::endl;
    std::cout << "\nBeton senzor:" << std::endl;
    std::cout << "  Temperatura: " << betonSensor.temperature << "°C" << std::endl;
    std::cout << "  Vlažnost: " << betonSensor.humidity << "%" << std::endl;
    std::cout << "  Baterija: " << betonSensor.battery << "%" << std::endl;
    std::cout << "  Ciljna vlažnost: " << getTargetHumidity() << "%" << std::endl;
    
    std::cout << "\nVazduh senzor:" << std::endl;
    std::cout << "  Temperatura: " << airSensor.temperature << "°C" << std::endl;
    std::cout << "  Vlažnost: " << airSensor.humidity << "%" << std::endl;
    std::cout << "  Baterija: " << airSensor.battery << "%" << std::endl;
    std::cout << "  Maks. razlika temp: " << getTargetTempDifference() << "°C" << std::endl;
    
    std::cout << "\nPumpa:" << std::endl;
    std::cout << "  Status: " << (pump.active ? "AKTIVNA" : "NEAKTIVNA") << std::endl;
    std::cout << "  Baterija: " << pump.battery << "%" << std::endl;
    
    std::cout << "\nGrijač:" << std::endl;
    std::cout << "  Status: " << (heater.active ? "AKTIVAN" : "NEAKTIVAN") << std::endl;
    std::cout << "  Temperatura: " << heater.temperature << "°C" << std::endl;
    std::cout << "  Baterija: " << heater.battery << "%" << std::endl;
    std::cout << "=========================\n" << std::endl;
}

void SystemController::printAlarms() const {
    std::cout << "\n===== ALARMI =====" << std::endl;
    if (alarms.empty()) {
        std::cout << "Nema aktivnih alarma" << std::endl;
    } else {
        for (const auto& alarm : alarms) {
            std::string levelStr;
            switch(alarm.level) {
                case AlarmLevel::INFO: 
                    levelStr = "INFO"; 
                    break;
                case AlarmLevel::WARNING: 
                    levelStr = "WARNING"; 
                    break;
                case AlarmLevel::CRITICAL: 
                    levelStr = "CRITICAL"; 
                    break;
                default: 
                    levelStr = "UNKNOWN"; 
                    break;
            }
            std::cout << "[" << levelStr << "] " << alarm.message << std::endl;
        }
    }
    std::cout << "==================\n" << std::endl;
}