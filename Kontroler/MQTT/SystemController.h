#ifndef SYSTEMCONTROLLER_H
#define SYSTEMCONTROLLER_H

#include <mosquitto.h>
#include <string>
#include <iostream>
#include <chrono>
#include <fstream>
#include <cmath>
#include <vector>
#include <algorithm>


// MQTT topici za pretplatu
#define BETON_TEMPERATURA   "ploca1/beton/temperatura"
#define BETON_VLAZNOST      "ploca1/beton/vlaznost"
#define BETON_BATERIJA      "ploca1/beton/baterija"
#define VAZDUH_TEMPERATURA  "ploca1/povrsina/temperatura"
#define VAZDUH_VLAZNOST     "ploca1/povrsina/vlaznost"
#define VAZDUH_BATERIJA     "ploca1/povrsina/baterija"
#define PUMPA_GRESKA        "ploca1/vodena_pumpa/ventil/greska"
#define PUMPA_BATERIJA      "ploca1/vodena_pumpa/baterija"
#define GREJAC_BATERIJA     "ploca1/grejac_vode/baterija"

// MQTT topici za objavljivanje
#define PUMPA_STATUS         "ploca1/vodena_pumpa/ventil/stanje"
#define PUMPA_VREME_RADA     "ploca1/vodena_pumpa/ventil/vreme_rada"
#define GREJAC_STATUS        "ploca1/grejac_vode/stanje"
#define GREJAC_TARGET_TEMP   "ploca1/grejac_vode/temperatura"

// Konfiguracioni parametri
#define MAX_PUMP_DURATION 1800 // 30 minuta u sekundama
#define MIN_PUMP_PAUSE 900 // 15 minuta u sekundama
#define MIN_CONCRETE_TEMP 5.0f
#define MAX_CONCRETE_TEMP 35.0f
#define CRITICAL_MIN_TEMP 0.0f
#define CRITICAL_MAX_TEMP 40.0f
#define MIN_AIR_TEMP_FOR_PUMP 2.0f
#define MIN_AIR_TEMP_FOR_HEATING 10.0f
#define LOW_BATTERY_THRESHOLD 20

#define PUMP_STATE_ON 1
#define PUMP_STATE_OFF 0
#define HEATER_STATE_ON 1
#define HEATER_STATE_OFF 0

// Strukture podataka za senzore i aktuatora i alarme
enum class AlarmLevel {
    INFO,
    WARNING,
    CRITICAL,
    UNKNOWN
};

struct Alarm {
    AlarmLevel level;
    std::string message;
    long long timestamp;
};

struct BetonSensor {
    float temperature = 0.0f;
    float humidity = 0.0f;
    int battery = 100;
    long long timestamp = 0;
};

struct AirSensor {
    float temperature = 0.0f;
    float humidity = 0.0f;
    int battery = 100;
    long long timestamp = 0;
};

struct Pump {
    int active = PUMP_STATE_OFF;
    int battery = 100;
    long long remaining_time = 0; // Preostalo vreme rada u MINUTAMA (usklađeno sa simulacijom)
    long long timestamp = 0;
    long long last_activation = 0; // Timestamp aktivacije (milisekunde)
    long long last_deactivation = 0; // Timestamp deaktivacije (milisekunde)
};

struct Heater {
    int active = HEATER_STATE_OFF;
    double temperature = 0.0;
    int battery = 100;
    long long timestamp = 0;
};

struct TimeConfig {
    std::string date;
    std::string time;
    int step_minutes;
    long long pour_timestamp; // Vreme izlivanja betona
    long long simulated_timestamp; // Trenutno simulirano vreme
    std::string config_filepath; // Putanja do time.json fajla
};

class SystemController {
private:
    struct mosquitto* mosq;
    
    BetonSensor betonSensor;
    AirSensor airSensor;
    Pump pump;
    Heater heater;
    TimeConfig timeConfig;
    
    std::vector<Alarm> alarms;
    
    
    long long getCurrentTimestamp() const;
    long long getConcreteAgeHours() const;
    float getTargetTempDifference() const;
    float getTargetHumidity() const;
    void addAlarm(AlarmLevel level, const std::string& message);
    void checkAlarms();
    bool canActivatePump() const;
    bool parseTimeConfig(const std::string& filepath);
    long long parseDateTime(const std::string& date, const std::string& time) const;
    
public:
    SystemController();
    ~SystemController();
    
    void controlSystem();
    
    bool connect(const std::string& broker, int port, int keepalive);
    void disconnect();
    bool isConnected() const;
    
    bool setPumpState(int active, int duration_minutes = 0);
    bool setHeaterState(int active, double target_temp = 0.0);
    
    bool loadTimeConfig(const std::string& filepath);
    bool updateSimulatedTime();
    
    void printStatus() const;
    void printAlarms() const;
    
    static void onConnect(struct mosquitto* mosq, void* obj, int result);
    static void onMessage(struct mosquitto* mosq, void* obj, const struct mosquitto_message* message);
};

#endif // SYSTEMCONTROLLER_H