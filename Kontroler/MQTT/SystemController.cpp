#include "SystemController.h"


#ifndef DEBUG
#define DEBUG 1
#endif

SystemController::SystemController() : mosq(nullptr) {
    mosquitto_lib_init();
    timeConfig.simulated_timestamp = 0;
    timeConfig.pour_timestamp = 0;
    timeConfig.step_minutes = 10;
}

SystemController::~SystemController() {
    disconnect();
    mosquitto_lib_cleanup();
}

bool SystemController::connect(const std::string& broker, int port, int keepalive) {
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
        mosquitto_subscribe(mosq, NULL, BETON_BATERIJA, 0);

        mosquitto_subscribe(mosq, NULL, VAZDUH_TEMPERATURA, 0);
        mosquitto_subscribe(mosq, NULL, VAZDUH_VLAZNOST, 0);
        mosquitto_subscribe(mosq, NULL, VAZDUH_BATERIJA, 0);

        mosquitto_subscribe(mosq, NULL, PUMPA_BATERIJA, 0);

        mosquitto_subscribe(mosq, NULL, GREJAC_BATERIJA, 0);

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
            else if (topic == BETON_BATERIJA) {
                int bat = std::stoi(payload);
                controller->betonSensor.battery = bat;
            }
            else if (topic == VAZDUH_TEMPERATURA) {
                controller->airSensor.temperature = std::stof(payload);
                controller->airSensor.timestamp = controller->getCurrentTimestamp();
            }
            else if (topic == VAZDUH_VLAZNOST) {
                controller->airSensor.humidity = std::stof(payload);
            }
            else if (topic == VAZDUH_BATERIJA) {
                controller->airSensor.battery = std::stoi(payload);
            }
            else if (topic == PUMPA_BATERIJA) {
                controller->pump.battery = std::stoi(payload);
                controller->pump.timestamp = controller->getCurrentTimestamp();
            }
            else if (topic == GREJAC_BATERIJA) {
                controller->heater.battery = std::stoi(payload);
            }
            else {
                std::cerr << "Nepoznat topic: " << topic << std::endl;
            }
        } catch (const std::exception& e) {
            std::cerr << "Greška pri parsiranju: " << e.what() << std::endl;
        }
    }
}

bool SystemController::setPumpState(int active, int duration_minutes) {
    if(!mosq) {
        std::cerr << "Niste povezani na MQTT broker." << std::endl;
        return false;
    }

    // Slanje stanja pumpe
    std::string state_str = std::to_string(active);

    // Vreme rada pumpe
    std::string duration_str = std::to_string(duration_minutes);

    int rc = mosquitto_publish(mosq, NULL, PUMPA_STATUS, state_str.size(), state_str.c_str(), 0, false);
    if(rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Greška pri slanju stanja pumpe: " << mosquitto_strerror(rc) << std::endl;
        return false;
    }

    // Ako je pumpa aktivirana, salje se i vreme rada
    if(active && duration_minutes > 0) {
        rc = mosquitto_publish(mosq, NULL, PUMPA_VREME_RADA, duration_str.size(), duration_str.c_str(), 0, false);
        pump.active = active;
        if(rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "Greška pri slanju vremena rada pumpe: " << mosquitto_strerror(rc) << std::endl;
            return false;
        }
        // Cuvanje vremena rada u minutima
        pump.remaining_time = duration_minutes;
    } else {
        rc = mosquitto_publish(mosq, NULL, PUMPA_VREME_RADA, duration_str.size(), duration_str.c_str(), 0, false);
        if(rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "Greška pri slanju vremena rada pumpe: " << mosquitto_strerror(rc) << std::endl;
            return false;
        }
        pump.remaining_time = 0;
   }
    if(DEBUG) {
        std:: cout << "Poslata komanda pumpi: " << active << (duration_minutes > 0 ? (" na " + std::to_string(duration_minutes) + " min") : "") << std::endl;
    }

    return true;
}

bool SystemController::setHeaterState(int active, double target_temp) {
    if(!mosq) {
        std::cerr << "Niste povezani na MQTT broker." << std::endl;
        return false;
    }
    // Slanje stanja grejača
    std::string state_str = std::to_string(active);

    // Ciljna temperatura
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
    }
    
    if(DEBUG) {
        std:: cout << "Poslata komanda grejaču: " << active << (active ? (" na " + std::to_string(target_temp) + "°C") : "") << std::endl;
    }

    return true;
}

// Pomoćna metoda za dobijanje trenutnog timestamp-a u milisekundama
// Koristi simulirano vreme ako je učitano, inače sistemsko vreme
long long SystemController::getCurrentTimestamp() const {
    if (timeConfig.simulated_timestamp > 0) {
        return timeConfig.simulated_timestamp;
    }
    // Fallback na sistemsko vreme ako simulacija nije učitana
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
}

long long SystemController::getConcreteAgeHours() const {
    if (timeConfig.pour_timestamp == 0) {
        return 0;
    }
    return (getCurrentTimestamp() - timeConfig.pour_timestamp) / (1000 * 3600); // Vreme u satima
}

float SystemController::getTargetTempDifference() const {
    long long age = getConcreteAgeHours();
    if (age <= 12) return 3.0f;
    else if (age <= 24) return 5.0f;
    else if (age <= 168) return 7.0f; // 1 - 7 dana
    else return 7.0f;
}

float SystemController::getTargetHumidity() const {
    long long age = getConcreteAgeHours();
    if (age <= 12) return 80.0f;
    else if (age <= 24) return 60.0f;
    else if (age <= 48) return 50.0f;
    else if (age <= 72) return 40.0f;
    else if (age <= 168) return 15.0f; // 3 - 7 dana
    else return 15.0f;
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
    float tempDiff = (betonSensor.temperature - airSensor.temperature);
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
    
    // Provera pauze između aktivacija (u minutama)
    if (pump.last_deactivation > 0) {
        long long timeSinceDeactivation_minutes = (getCurrentTimestamp() - pump.last_deactivation) / (1000 * 60);
        if (timeSinceDeactivation_minutes < MIN_PUMP_PAUSE) {
            return false;
        }
    }
    
    // Provera maksimalnog trajanja (u minutama)
    if (pump.active) {
        long long activeDuration_minutes = (getCurrentTimestamp() - pump.last_activation) / (1000 * 60);
        if (activeDuration_minutes >= MAX_PUMP_DURATION) {
            return false;
        }
    }
    
    return true;
}

void SystemController::controlSystem() {
    
    checkAlarms();
    
    float targetHumidity = getTargetHumidity();
    
    // Provere uslova
    bool needsWater = betonSensor.humidity < targetHumidity; // Vlažnost betona ispod ciljne vrednosti
    bool airTooHumid = airSensor.humidity < 50.0f; // Da li je vlažnost vazduha ispod 50%
    bool needsCooling = betonSensor.temperature > MAX_CONCRETE_TEMP; // Previsoka temperatura betona
    bool needsHeating = betonSensor.temperature < MIN_CONCRETE_TEMP; // Preniska temperatura betona
    bool airTooCold = airSensor.temperature < MIN_AIR_TEMP_FOR_HEATING; // Da li je temperatura vazduha preniska za grejanje
    
    bool shouldActivatePump = (needsWater || airTooHumid || needsCooling) && canActivatePump();
    
    // Grejač treba da radi ako:
    // 1. Temperatura betona je niska ILI
    // 2. Temperatura vazduha je niska I potrebno je poljevanje
    bool shouldActivateHeater = needsHeating || (airTooCold && shouldActivatePump);
    
    // Kontrola grejača
    if (shouldActivateHeater) {
        if (heater.active == HEATER_STATE_OFF) {
            double targetTemp = needsHeating ? MIN_CONCRETE_TEMP + 5.0 : 25;
            setHeaterState(HEATER_STATE_ON, targetTemp);
            if (DEBUG) {
                std::cout << "\n[GREJAČ] Aktiviran - " 
                          << (needsHeating ? "grejanje betona" : "grejanje vode za poljevanje")
                          << " (ciljna temp: " << targetTemp << "°C)" << std::endl;
            }
        }
    } else {
        if (heater.active == HEATER_STATE_ON) {
            setHeaterState(HEATER_STATE_OFF, 0);
            if (DEBUG) {
                std::cout << "\n[GREJAČ] Isključen" << std::endl;
            }
        }
    }
    
    // Kontrola pumpe - provera da li je prošlo postavljeno vreme rada
    if (pump.active == PUMP_STATE_ON && pump.remaining_time > 0) {
        // Računanje prošlog vremena u MINUTAMA (simulirano vreme)
        long long current_timestamp = getCurrentTimestamp();
        long long activeDuration_ms = current_timestamp - pump.last_activation;
        long long activeDuration_minutes = activeDuration_ms / (1000 * 60);
        
        // Ako je prošlo postavljeno vreme rada, isključi pumpu
        if (activeDuration_minutes >= pump.remaining_time) {
            if (DEBUG) {
                std::cout << "\n[PUMPA] Vreme rada pumpe je isteklo!" << std::endl;
                std::cout << "  - Postavljeno: " << pump.remaining_time << " min" << std::endl;
                std::cout << "  - Prošlo: " << activeDuration_minutes << " min" << std::endl;
                std::cout << "  - Isključujem pumpu..." << std::endl;
            }
            setPumpState(PUMP_STATE_OFF, 0);
            pump.last_deactivation = getCurrentTimestamp();
            pump.remaining_time = 0;
        } else {
            if (DEBUG) {
                long long remaining = pump.remaining_time - activeDuration_minutes;
                std::cout << "\n[PUMPA] Status rada:" << std::endl;
                std::cout << "  - Postavljeno vreme: " << pump.remaining_time << " min" << std::endl;
                std::cout << "  - Proteklo vreme: " << activeDuration_minutes << " min" << std::endl;
                std::cout << "  - Preostalo vreme: " << remaining << " min" << std::endl;
            }
        }
    }
    // Kontrola pumpe - uključivanje po potrebi
    else if (shouldActivatePump && pump.active == PUMP_STATE_OFF) {
        int duration = 300; // 5 minuta početno
        if (betonSensor.humidity < targetHumidity) {
            duration = 600; // 10 minuta za veliku razliku
        }
        
        if (DEBUG) {
            std::cout << "\n[PUMPA] Aktiviranje pumpe" << std::endl;
            std::cout << "  - Razlozi: ";
            if (needsWater) std::cout << "niska vlažnost betona ";
            if (airTooHumid) std::cout << "niska vlažnost vazduha ";
            if (needsCooling) std::cout << "hlađenje ";
            std::cout << std::endl;
            std::cout << "  - Postavljeno vreme rada: " << duration << " min" << std::endl;
            if (heater.active == HEATER_STATE_ON) {
                std::cout << "  - Grejač AKTIVAN - voda će biti zagrejana" << std::endl;
            }
        }
        
        setPumpState(PUMP_STATE_ON, duration);
        pump.last_activation = getCurrentTimestamp();
    }
    // Dodatna provera za isključivanje pumpe
    else if (pump.active == PUMP_STATE_ON) {
        long long activeDuration_ms = getCurrentTimestamp() - pump.last_activation;
        long long activeDuration_minutes = activeDuration_ms / (1000 * 60);
        
        // Isključi ako je dostignut maksimum ili više nije potrebna
        bool shouldDeactivate = (activeDuration_minutes >= MAX_PUMP_DURATION) || 
                                (!needsWater && !airTooHumid && !needsCooling);
        
        if (shouldDeactivate) {
            if (DEBUG) {
                std::cout << "\n[PUMPA] Isključujem pumpu - ";
                if (activeDuration_minutes >= MAX_PUMP_DURATION) {
                    std::cout << "maksimalno trajanje dostignuto";
                } else {
                    std::cout << "više nije potrebna";
                }
                std::cout << std::endl;
            }
            setPumpState(PUMP_STATE_OFF, 0);
            pump.last_deactivation = getCurrentTimestamp();
            pump.remaining_time = 0;
        }
    }
}

bool SystemController::loadTimeConfig(const std::string& filepath) {
    timeConfig.config_filepath = filepath;
    if (!parseTimeConfig(filepath)) {
        return false;
    }
    
    // Postavi pour_timestamp na učitano simulirano vreme (početak)
    timeConfig.pour_timestamp = timeConfig.simulated_timestamp;
    
    std::cout << "Učitana konfiguracija vremena: " << timeConfig.date 
              << " " << timeConfig.time << std::endl;
    std::cout << "Pour timestamp postavljen na: " << timeConfig.pour_timestamp << std::endl;
    return true;
}

bool SystemController::parseTimeConfig(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Nije moguće otvoriti fajl: " << filepath << std::endl;
        return false;
    }
    
    std::string line;
    std::string date_val, time_val;
    int step_val = 10;
    
    // Jednostavno parsiranje JSON fajla bez eksternih biblioteka
    while (std::getline(file, line)) {
        // Ukloni razmake
        line.erase(std::remove(line.begin(), line.end(), ' '), line.end());
        line.erase(std::remove(line.begin(), line.end(), '\t'), line.end());
        
        // Traži "date":"value"
        size_t date_pos = line.find("\"date\":");
        if (date_pos != std::string::npos) {
            size_t start = line.find("\"", date_pos + 7);
            size_t end = line.find("\"", start + 1);
            if (start != std::string::npos && end != std::string::npos) {
                date_val = line.substr(start + 1, end - start - 1);
            }
        }
        
        // Traži "time":"value"
        size_t time_pos = line.find("\"time\":");
        if (time_pos != std::string::npos) {
            size_t start = line.find("\"", time_pos + 7);
            size_t end = line.find("\"", start + 1);
            if (start != std::string::npos && end != std::string::npos) {
                time_val = line.substr(start + 1, end - start - 1);
            }
        }
        
        // Traži "step_minutes":value
        size_t step_pos = line.find("\"step_minutes\":");
        if (step_pos != std::string::npos) {
            size_t start = step_pos + 15;
            size_t end = line.find_first_not_of("0123456789", start);
            if (start != std::string::npos) {
                std::string step_str = line.substr(start, end - start);
                if (!step_str.empty()) {
                    step_val = std::stoi(step_str);
                }
            }
        }
    }
    
    file.close();
    
    if (date_val.empty() || time_val.empty()) {
        std::cerr << "Greška: Nije moguće parsirati date ili time iz JSON fajla" << std::endl;
        return false;
    }
    
    timeConfig.date = date_val;
    timeConfig.time = time_val;
    timeConfig.step_minutes = step_val;
    timeConfig.simulated_timestamp = parseDateTime(date_val, time_val);
    
    return true;
}

long long SystemController::parseDateTime(const std::string& date, const std::string& time) const {
    // Parsiraj datum: "npr. 2025-05-06"
    int year = 0, month = 0, day = 0;
    if (sscanf(date.c_str(), "%d-%d-%d", &year, &month, &day) != 3) {
        std::cerr << "Greška pri parsiranju datuma: " << date << std::endl;
        return 0;
    }
    
    // Parsiraj vreme: "npr. 21:40:00"
    int hour = 0, minute = 0, second = 0;
    if (sscanf(time.c_str(), "%d:%d:%d", &hour, &minute, &second) != 3) {
        std::cerr << "Greška pri parsiranju vremena: " << time << std::endl;
        return 0;
    }
    
    // Konvertuj u timestamp (milisekunde od Unix epoch-a)
    // Jednostavna aproksimacija - računa dane od 1970-01-01
    int days_from_epoch = 0;
    
    // Dodaj dane za godine
    for (int y = 1970; y < year; y++) {
        if ((y % 4 == 0 && y % 100 != 0) || (y % 400 == 0)) {
            days_from_epoch += 366; // Prestupna godina
        } else {
            days_from_epoch += 365;
        }
    }
    
    // Dodaj dane za mesece u trenutnoj godini
    int days_in_month[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0)) {
        days_in_month[1] = 29; // Februar u prestupnoj godini
    }
    
    for (int m = 0; m < month - 1; m++) {
        days_from_epoch += days_in_month[m];
    }
    
    // Dodaj dane u trenutnom mesecu
    days_from_epoch += day - 1;
    
    // Konvertuj sve u milisekunde
    long long timestamp = (long long)days_from_epoch * 24LL * 3600LL * 1000LL;
    timestamp += (long long)hour * 3600LL * 1000LL;
    timestamp += (long long)minute * 60LL * 1000LL;
    timestamp += (long long)second * 1000LL;
    
    return timestamp;
}

bool SystemController::updateSimulatedTime() {
    if (timeConfig.config_filepath.empty()) {
        std::cerr << "Config filepath nije postavljen. Prvo pozovite loadTimeConfig()." << std::endl;
        return false;
    }
    
    long long old_timestamp = timeConfig.simulated_timestamp;
    bool result = parseTimeConfig(timeConfig.config_filepath);
    
    if (result && DEBUG) {
        long long time_diff_ms = timeConfig.simulated_timestamp - old_timestamp;
        long long time_diff_minutes = time_diff_ms / (1000 * 60);
        if (time_diff_ms != 0) {
            std::cout << "\n[VREME AŽURIRANO] " << timeConfig.date << " " << timeConfig.time 
                      << " (+" << time_diff_minutes << " min)" << std::endl;
        }
    }
    
    return result;
}

void SystemController::printStatus() const {
    std::cout << "\n===== STATUS SISTEMA =====" << std::endl;
    std::cout << "Simulirano vreme: " << timeConfig.date << " " << timeConfig.time << std::endl;
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
    
    if (pump.active) {
        if (pump.remaining_time > 0) {
            long long elapsed_minutes = (getCurrentTimestamp() - pump.last_activation) / (1000 * 60);
            long long remaining = pump.remaining_time - elapsed_minutes;
            
            std::cout << "  Postavljeno vreme rada: " << pump.remaining_time << " min" << std::endl;
            std::cout << "  Proteklo vreme: " << elapsed_minutes << " min" << std::endl;
            
            if (remaining > 0) {
                std::cout << "  Preostalo vreme: " << remaining << " min" << std::endl;
            } else {
                std::cout << "  Preostalo vreme: 0 min (vreme je isteklo!)" << std::endl;
            }
        } else {
            std::cout << "  Vreme rada: nije postavljeno" << std::endl;
        }
    }
    
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