#ifndef PARSE_H
#define PARSE_H

#include <string>
#include "../../common/file_mutex.h"

struct ActuatorData {
    int baterija;
    int aktivan;
    int vreme_rada; // Vreme rada u MINUTAMA (usklađeno sa simulacijom)
};

std::string readJsonFromFile(const std::string& filename);
int readBatteryFromFile(const std::string& filename = "../../SimData/BATERIJE.JSON");
void parseStateMessage(const std::string& message);
void parseDurationMessage(const std::string& message);
void writePumpJsonToFile(const ActuatorData& data, const std::string& filename = "../../SimData/AKTUATORI.JSON");

// Eksterna promenljiva za stanje aktuatora
extern ActuatorData currentActuatorData;

#endif // PARSE_H
