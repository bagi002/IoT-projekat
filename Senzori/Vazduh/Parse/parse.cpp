#include "parse.h"
#include <fstream>

// Funckija za parsiranje jednostavnog JSON formata
SensorData parseJsonData(const std::string& jsonStr) {
    SensorData data = {};
    
    // Parsiranje temperature
    size_t tempPos = jsonStr.find("\"temperatura\":");
    if (tempPos != std::string::npos) {
        size_t start = jsonStr.find_first_of("0123456789.-", tempPos);
        size_t end = jsonStr.find_first_of(",}", start);
        if (start != std::string::npos && end != std::string::npos) {
            data.temperatura = std::stod(jsonStr.substr(start, end - start));
        }
    }
    
    // Parsiranje vlaznosti
    size_t vlazPos = jsonStr.find("\"vlaznost\":");
    if (vlazPos != std::string::npos) {
        size_t start = jsonStr.find_first_of("0123456789.-", vlazPos);
        size_t end = jsonStr.find_first_of(",}", start);
        if (start != std::string::npos && end != std::string::npos) {
            data.vlaznost = std::stod(jsonStr.substr(start, end - start));
        }
    }
    
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

// Funkcija za čitanje JSON podataka iz datoteke
std::string readJsonFromFile(const std::string& filename) {
    std::ifstream file(filename);
    std::string line;
    if (std::getline(file, line)) {
        return line;
    }
    return "";
}
