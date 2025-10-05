#include "parse.h"
#include <fstream>
#include <iostream>

#ifndef DEBUG
#define DEBUG 1
#endif

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

// Funkcija za čitanje podataka o bateriji iz BATERIJE.json
int readBatteryFromFile(const std::string& filename) {
    std::string jsonData = readJsonFromFile(filename);
    if (!jsonData.empty()) {
        // Parsiranje heater_battery
        size_t batPos = jsonData.find("\"heater_battery\":");
        if (batPos != std::string::npos) {
            size_t start = jsonData.find_first_of("0123456789", batPos);
            size_t end = jsonData.find_first_of(",}", start);
            if (start != std::string::npos && end != std::string::npos) {
                return std::stoi(jsonData.substr(start, end - start));
            }
        }
    }
    return 0; // Default value ako nema podataka
}

// Funkcija za parsiranje state poruke od kontrolera
void parseStateMessage(const std::string& message) {
    if (message == "1") {
        currentActuatorData.aktivan = 1;
    } else if (message == "0") {
        currentActuatorData.aktivan = 0;
    }
}

// Funkcija za parsiranje temperature od kontrolera
void parseTemperatureMessage(const std::string& message) {
    try {
        currentActuatorData.temperatura = std::stod(message);
    } catch (const std::exception& e) {
        std::cerr << "Greška pri parsiranju temperature: " << e.what() << std::endl;
    }
}

// Funkcija za kreiranje i pisanje JSON datoteke sa stanjem grejača i ciljnom temperaturom
void writeGrejacJsonToFile(const ActuatorData& data, const std::string& filename) {
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
    
    // Sada prepiši fajl sa ažuriranim heater delom
    std::ofstream file(filename);
    if (file.is_open()) {
        // Ako je fajl prazan, kreiraj početni JSON
        if (existingContent.empty() || existingContent.find_first_not_of(" \t\n\r{}") == std::string::npos) {
            file << "{\n";
            file << "    \"heater\": {\n";
            file << "        \"status\": " << data.aktivan << ",\n";
            file << "        \"temperature\": " << data.temperatura << "\n";
            file << "    }\n";
            file << "}\n";
        } else {
            // Pronađi heater entry i zameni samo njegovu vrednost
            size_t heaterPos = existingContent.find("\"heater\"");
            if (heaterPos != std::string::npos) {
                // Pronađi početak heater objekta
                size_t startObj = existingContent.find("{", heaterPos);
                if (startObj != std::string::npos) {
                    // Pronađi kraj heater objekta
                    int braceCount = 1;
                    size_t endObj = startObj + 1;
                    while (endObj < existingContent.length() && braceCount > 0) {
                        if (existingContent[endObj] == '{') braceCount++;
                        else if (existingContent[endObj] == '}') braceCount--;
                        endObj++;
                    }
                    
                    // Zameni heater entry sa novim vrednostima
                    std::string before = existingContent.substr(0, heaterPos);
                    std::string after = existingContent.substr(endObj);
                    
                    file << before << "\"heater\": {\n";
                    file << "        \"status\": " << data.aktivan << ",\n";
                    file << "        \"temperature\": " << data.temperatura << "\n";
                    file << "    }" << after;
                }
            } else {
                // Dodaj heater entry ako ne postoji, ali sačuvaj sve postojeće podatke
                size_t firstBrace = existingContent.find_first_of('{');
                size_t lastBrace = existingContent.find_last_of('}');
                
                if (firstBrace != std::string::npos && lastBrace != std::string::npos) {
                    // Izvuci sadržaj između zagrada (postojeći objekti kao pump)
                    std::string innerContent = existingContent.substr(firstBrace + 1, lastBrace - firstBrace - 1);
                    
                    // Ukloni trailing whitespace
                    size_t lastNonWhitespace = innerContent.find_last_not_of(" \t\n\r");
                    if (lastNonWhitespace != std::string::npos) {
                        innerContent = innerContent.substr(0, lastNonWhitespace + 1);
                    }
                    
                    // Proveri da li postoje neki podaci (npr. pump)
                    bool hasExistingData = innerContent.find("\"pump\"") != std::string::npos;
                    
                    file << "{\n";
                    
                    if (hasExistingData) {
                        // Prvo dodaj postojeće podatke (pump), pa onda heater
                        file << innerContent << ",\n";
                    }
                    
                    file << "    \"heater\": {\n";
                    file << "        \"status\": " << data.aktivan << ",\n";
                    file << "        \"temperature\": " << data.temperatura << "\n";
                    file << "    }\n";
                    file << "}\n";
                }
            }
        }
        file.close();
        if (DEBUG) {
            std::cout << "Stanje grejača zapisano u " << filename << std::endl;
        }
    } else {
        std::cerr << "Greška pri pisanju u datoteku " << filename << std::endl;
    }
}