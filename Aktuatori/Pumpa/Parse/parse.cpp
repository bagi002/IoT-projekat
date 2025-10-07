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
// Očekuje se vreme u MINUTAMA
void parseDurationMessage(const std::string& message) {
    try {
        currentActuatorData.vreme_rada = std::stoi(message);
    } catch (const std::exception& e) {
        std::cerr << "Greška pri parsiranju vremena rada: " << e.what() << std::endl;
    }
}

// Funkcija za kreiranje i pisanje JSON fajla sa stanjem vodene pumpe i vremenom rada
// Format {"pump": {"status": 1/0, "runtime_minutes": int}}
void writePumpJsonToFile(const ActuatorData& data, const std::string& filename) {
    std::lock_guard<std::mutex> lock(aktuatori_file_mutex); // Zaključavanje mutex-a
    
    std::ifstream inFile(filename);
    std::string existingContent = "";
    
    // Učitaj ceo sadržaj fajla
    if (inFile.is_open()) {
        std::string line;
        while (std::getline(inFile, line)) {
            existingContent += line + "\n";
        }
        inFile.close();
    }
    
    // Pronađi pump entry i zameni samo njegovu vrednost
    size_t pumpPos = existingContent.find("\"pump\"");
    if (pumpPos != std::string::npos) {
        // Pronađi početak pump objekta (zagrada nakon "pump":)
        size_t startObj = existingContent.find("{", pumpPos);
        if (startObj != std::string::npos) {
            // Pronađi kraj pump objekta - zatvarajuću zagradu
            int braceCount = 1;
            size_t endObj = startObj + 1;
            while (endObj < existingContent.length() && braceCount > 0) {
                if (existingContent[endObj] == '{') braceCount++;
                else if (existingContent[endObj] == '}') braceCount--;
                endObj++;
            }
            
            // 'before' sadrži sve pre "pump" (uključujući otvarajuću { glavnog objekta)
            // 'after' sadrži sve nakon zatvarajuće } pump objekta (zarez, heater, itd.)
            std::string before = existingContent.substr(0, pumpPos);
            std::string after = existingContent.substr(endObj);
            
            // vreme_rada je već u minutama - direktno koristimo
            int runtime_minutes = data.vreme_rada;
            
            // Prepiši fajl sa ažuriranim pump delom
            std::ofstream file(filename);
            if (file.is_open()) {
                file << before << "\"pump\": {\n";
                file << "    \"status\": " << data.aktivan << ",\n";
                file << "    \"runtime_minutes\": " << runtime_minutes << "\n";
                file << "  }" << after;
                file.close();
                
                if (DEBUG) {
                    std::cout << "Stanje vodene pumpe zapisano u " << filename 
                              << " (runtime: " << runtime_minutes << " min)" << std::endl;
                }
            } else {
                std::cerr << "Greška pri pisanju u datoteku " << filename << std::endl;
            }
        }
    } else {
        std::cerr << "Greška: pump sekcija ne postoji u " << filename << std::endl;
    }
}
