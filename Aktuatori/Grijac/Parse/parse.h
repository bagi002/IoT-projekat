#ifndef PARSE_H
#define PARSE_H

#include <string>
#include "../../common/file_mutex.h"

struct ActuatorData {
    int baterija;
    bool hasGreska;
    std::string greska;
    int aktivan;
    double temperatura;
};

// Deklaracije funkcija
std::string readJsonFromFile(const std::string& filename);
int readBatteryFromFile(const std::string& filename = "../../simulacija/BATERIJE.json");
void parseStateMessage(const std::string& message);
void parseTemperatureMessage(const std::string& message);
void writeGrejacJsonToFile(const ActuatorData& data, const std::string& filename = "../../simulacija/AKTUATORI.json");

// Eksterna varijabla
extern ActuatorData currentActuatorData;

#endif // PARSE_H
