#ifndef PARSE_H
#define PARSE_H

#include <string>
#include "../../common/file_mutex.h"

struct ActuatorData {
    int baterija;
    int aktivan;
    int vreme_rada;
};

std::string readJsonFromFile(const std::string& filename);
int readBatteryFromFile(const std::string& filename = "/home/radov1c/Desktop/FTN/Letnji/IoT/IoT-projekat/simulacija/SimData/BATERIJE.JSON");
void parseStateMessage(const std::string& message);
void parseDurationMessage(const std::string& message);
void writePumpJsonToFile(const ActuatorData& data, const std::string& filename = "/home/radov1c/Desktop/FTN/Letnji/IoT/IoT-projekat/simulacija/SimData/AKTUATORI.JSON");

// Eksterna promenljiva za stanje aktuatora
extern ActuatorData currentActuatorData;

#endif // PARSE_H
