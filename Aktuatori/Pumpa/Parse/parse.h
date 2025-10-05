#ifndef PARSE_H
#define PARSE_H

#include <string>
#include "../../common/file_mutex.h"

struct ActuatorData {
    int baterija;
    bool hasGreska;
    std::string greska;
    int aktivan;
    int vreme_rada;
};

std::string readJsonFromFile(const std::string& filename);
int readBatteryFromFile(const std::string& filename = "../../simulacija/BATERIJE.json");
void parseStateMessage(const std::string& message);
void parseDurationMessage(const std::string& message);
void writePumpJsonToFile(const ActuatorData& data, const std::string& filename = "../../simulacija/AKTUATORI.json");

// Eksterna promenljiva za stanje aktuatora
extern ActuatorData currentActuatorData;

#endif // PARSE_H
