#include "parse.h"
#include <iostream>
#include <fstream>
#include <string>

#ifndef DEBUG
#define DEBUG 1
#endif



// Funkcija za citanje JSON sadržaja iz datoteke
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

// Funkcija za citanje podataka o bateriji iz BATERIJE.json
int readBatteryFromFile(const std::string& filename) {
    std::string jsonData = readJsonFromFile(filename);
    if (!jsonData.empty()) {
        size_t batPos = jsonData.find("\"pump_battery\":");
        if (batPos != std::string::npos) {
            size_t start = jsonData.find_first_of("0123456789", batPos);
            size_t end = jsonData.find_first_of(",}", start);
            if (start != std::string::npos && end != std::string::npos) {
                return std::stoi(jsonData.substr(start, end - start));
            }
        }
    }
    return 0;
}

// Funkcija za parsiranje poruke o stanju iz kontrolera
void parseStateMessage(const std::string& message) {
    if (message == "1") {
        currentActuatorData.aktivan = 1;
    } else if (message == "0") {
        currentActuatorData.aktivan = 0;
    }
}

// Funkcija za parsiranje trajanja aktivnosti pumpe iz kontrolera
void parseDurationMessage(const std::string& message) {
    try {
        currentActuatorData.vreme_rada = std::stoi(message);
    } catch (const std::exception& e) {
        std::cerr << "Greška pri parsiranju vremena rada: " << e.what() << std::endl;
    }
}

// Funkcija za kreiranje i pisanje JSON fajla sa stanjem vodene pumpe i vremenom rada
// Format {"pump": {"status": 1/0, "runtime_seconds": int}}
void writePumpJsonToFile(const ActuatorData& data, const std::string& filename) {
    std::ifstream inFile(filename);
    std::string existingContent = "";
    
    // Read existing content
    if (inFile.is_open()) {
        std::string line;
        while (std::getline(inFile, line)) {
            existingContent += line;
        }
        inFile.close();
    }
    
    std::ofstream file(filename);
    if (file.is_open()) {
        // If file was empty or contains only {}
        if (existingContent.empty() || existingContent.find_first_not_of(" \t\n\r{}") == std::string::npos) {
            file << "{\n    \"pump\": {\"status\": " << data.aktivan 
                 << ", \"runtime_seconds\": " << data.vreme_rada << "}\n}";
        } else {
            // Find existing pump entry and replace it
            size_t pumpPos = existingContent.find("\"pump\"");
            if (pumpPos != std::string::npos) {
                // Find start of pump object
                size_t startObj = existingContent.find("{", pumpPos);
                if (startObj != std::string::npos) {
                    // Find end of pump object
                    int braceCount = 1;
                    size_t endObj = startObj + 1;
                    while (endObj < existingContent.length() && braceCount > 0) {
                        if (existingContent[endObj] == '{') braceCount++;
                        else if (existingContent[endObj] == '}') braceCount--;
                        endObj++;
                    }
                    
                    // Replace pump entry
                    std::string before = existingContent.substr(0, pumpPos);
                    std::string after = existingContent.substr(endObj);
                    
                    file << before << "\"pump\": {\"status\": " << data.aktivan 
                         << ", \"runtime_seconds\": " << data.vreme_rada << "}" << after;
                }
            } else {
                // Add pump entry if it doesn't exist
                size_t lastBrace = existingContent.find_last_of('}');
                if (lastBrace != std::string::npos) {
                    std::string beforeBrace = existingContent.substr(0, lastBrace);
                    // Add comma if data already exists
                    if (beforeBrace.find_first_not_of(" \t\n\r{") != std::string::npos) {
                        file << beforeBrace << ",\n    \"pump\": {\"status\": " << data.aktivan 
                             << ", \"runtime_seconds\": " << data.vreme_rada << "}\n}";
                    } else {
                        file << "{\n    \"pump\": {\"status\": " << data.aktivan 
                             << ", \"runtime_seconds\": " << data.vreme_rada << "}\n}";
                    }
                }
            }
        }
        file.close();
        if (DEBUG) {
            std::cout << "Stanje vodene pumpe zapisano u " << filename << std::endl;
        }
    } else {
        std::cerr << "Greška pri pisanju u datoteku " << filename << std::endl;
    }
}
