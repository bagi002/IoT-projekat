#include "parse.h"
#include <fstream>

// Funckija za parsiranje jednostavnog JSON formata
SensorData parseJsonData(const std::string& jsonStr) {
    SensorData data = {};
    
    // Parsiranje temperature (može biti negativna)
    size_t tempPos = jsonStr.find("\"temperature\":");
    if (tempPos != std::string::npos) {
        size_t start = jsonStr.find_first_of("-0123456789", tempPos);
        size_t end = jsonStr.find_first_of(",}\n", start);
        if (start != std::string::npos && end != std::string::npos) {
            data.temperatura = std::stod(jsonStr.substr(start, end - start));
        }
    }
    
    // Parsiranje vlažnosti
    size_t vlazPos = jsonStr.find("\"humidity\":");
    if (vlazPos != std::string::npos) {
        size_t start = jsonStr.find_first_of("0123456789", vlazPos);
        size_t end = jsonStr.find_first_of(",}\n", start);
        if (start != std::string::npos && end != std::string::npos) {
            data.vlaznost = std::stod(jsonStr.substr(start, end - start));
        }
    }
    
    // Parsiranje baterije (battery_level je decimalan broj, konvertujemo u ceo broj)
    size_t batPos = jsonStr.find("\"battery_level\":");
    if (batPos != std::string::npos) {
        size_t start = jsonStr.find_first_of("0123456789", batPos);
        size_t end = jsonStr.find_first_of(",}\n", start);
        if (start != std::string::npos && end != std::string::npos) {
            // Parsiramo kao double pa konvertujemo u int
            double batteryDouble = std::stod(jsonStr.substr(start, end - start));
            data.baterija = static_cast<int>(batteryDouble);
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
    std::string content;
    std::string line;
    
    if (file.is_open()) {
        while (std::getline(file, line)) {
            content += line;
        }
        file.close();
    }
    
    return content;
}
