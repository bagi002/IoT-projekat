#ifndef PARSE_H
#define PARSE_H

#include <string>
#include "../../common/file_mutex.h"

struct ActuatorData {
    int baterija;
    int aktivan;
    double temperatura;
};

// Deklaracije funkcija
std::string readJsonFromFile(const std::string& filename);
int readBatteryFromFile(const std::string& filename = "/home/radov1c/Desktop/FTN/Letnji/IoT/IoT-projekat/simulacija/SimData/BATERIJE.JSON");
void parseStateMessage(const std::string& message);
void parseTemperatureMessage(const std::string& message);
void writeGrejacJsonToFile(const ActuatorData& data, const std::string& filename = "/home/radov1c/Desktop/FTN/Letnji/IoT/IoT-projekat/simulacija/SimData/AKTUATORI.JSON");

// Eksterna varijabla
extern ActuatorData currentActuatorData;

#endif // PARSE_H
