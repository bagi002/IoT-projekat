#ifndef PARSE_H
#define PARSE_H

#include <string>

struct SensorData {
    double temperatura;
    double vlaznost;
    int baterija;
};

// Function declarations
SensorData parseJsonData(const std::string& jsonStr);
std::string readJsonFromFile(const std::string& filename);

#endif // PARSE_H
