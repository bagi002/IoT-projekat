#include "HttpServer.h"
#include "SystemController.h"
#include <iostream>
#include <cstring>
#include <sstream>
#include <iomanip>

HttpServer::HttpServer(int port) : daemon(nullptr), port(port), controller(nullptr) {
}

HttpServer::~HttpServer() {
    stop();
}

bool HttpServer::start(SystemController* ctrl) {
    if (daemon) {
        std::cerr << "HTTP server već pokrenut." << std::endl;
        return false;
    }
    
    if (!ctrl) {
        std::cerr << "SystemController pointer je null." << std::endl;
        return false;
    }
    
    controller = ctrl;
    
    daemon = MHD_start_daemon(
        MHD_USE_THREAD_PER_CONNECTION,
        port,
        NULL, NULL,
        &HttpServer::handleRequest, this,
        MHD_OPTION_END
    );
    
    if (!daemon) {
        std::cerr << "Greška pri pokretanju HTTP servera na portu " << port << std::endl;
        return false;
    }
    
    std::cout << "HTTP server pokrenut na portu " << port << std::endl;
    return true;
}

void HttpServer::stop() {
    if (daemon) {
        MHD_stop_daemon(daemon);
        daemon = nullptr;
        std::cout << "HTTP server zaustavljen." << std::endl;
    }
}

bool HttpServer::isRunning() const {
    return daemon != nullptr;
}

MHD_Result HttpServer::handleRequest(void* cls, struct MHD_Connection* connection,
                                     const char* url, const char* method,
                                     const char* version, const char* upload_data,
                                     size_t* upload_data_size, void** con_cls) {
    HttpServer* server = static_cast<HttpServer*>(cls);
    
    // Provera da li je prvi poziv (inicijalizacija)
    if (*con_cls == nullptr) {
        *con_cls = (void*)1;
        return MHD_YES;
    }
    
    std::string urlStr(url);
    std::string methodStr(method);
    
    std::cout << "HTTP " << methodStr << " " << urlStr << std::endl;
    
    std::string response;
    int status_code = 200;
    
    // Obrada GET zahteva
    if (methodStr == "GET") {
        if (urlStr == "/api/senzori/beton") {
            response = server->handleBetonSensor();
        }
        else if (urlStr == "/api/senzori/povrsina") {
            response = server->handlePovrsinaSensor();
        }
        else if (urlStr == "/api/pumpa/stanje") {
            response = server->handlePumpaStatus();
        }
        else if (urlStr == "/api/grijac/stanje") {
            response = server->handleGrijacStatus();
        }
        else if (urlStr == "/api/greske") {
            response = server->handleErrors();
        }
        else {
            response = "{\"error\": \"Endpoint nije pronađen\"}";
            status_code = 404;
        }
    }
    // Obrada POST zahteva
    else if (methodStr == "POST") {
        // POST /api/greska i POST /api/greske vraćaju listu grešaka (alarma)
        if (urlStr == "/api/greska" || urlStr == "/api/greske") {
            response = server->handleErrors();
        }
        else {
            response = "{\"error\": \"Endpoint nije pronađen\"}";
            status_code = 404;
        }
    }
    // Obrada OPTIONS zahteva (za CORS)
    else if (methodStr == "OPTIONS") {
        response = "{}";
        status_code = 200;
    }
    else {
        response = "{\"error\": \"Metoda nije podržana\"}";
        status_code = 405;
    }
    
    return server->sendResponse(connection, response, status_code);
}

MHD_Result HttpServer::sendResponse(struct MHD_Connection* connection, const std::string& json, int status_code) {
    struct MHD_Response* response = MHD_create_response_from_buffer(
        json.length(),
        (void*)json.c_str(),
        MHD_RESPMEM_MUST_COPY
    );
    
    if (!response) {
        return MHD_NO;
    }
    
    // Dodaj CORS headers
    MHD_add_response_header(response, "Content-Type", "application/json");
    MHD_add_response_header(response, "Access-Control-Allow-Origin", "*");
    MHD_add_response_header(response, "Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    MHD_add_response_header(response, "Access-Control-Allow-Headers", "Content-Type");
    
    MHD_Result ret = MHD_queue_response(connection, status_code, response);
    MHD_destroy_response(response);
    
    return ret;
}

std::string HttpServer::handleBetonSensor() {
    if (!controller) {
        return "{\"error\": \"Controller nije dostupan\"}";
    }
    
    auto data = controller->getBetonSensorData();
    
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(1);
    oss << "{"
        << "\"temperatura\": " << data.temperature << ", "
        << "\"vlaznost\": " << data.humidity << ", "
        << "\"baterija\": " << data.battery << ", "
        << "\"greska\": null"
        << "}";
    
    return oss.str();
}

std::string HttpServer::handlePovrsinaSensor() {
    if (!controller) {
        return "{\"error\": \"Controller nije dostupan\"}";
    }
    
    auto data = controller->getAirSensorData();
    
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(1);
    oss << "{"
        << "\"temperatura\": " << data.temperature << ", "
        << "\"vlaznost\": " << data.humidity << ", "
        << "\"baterija\": " << data.battery << ", "
        << "\"greska\": null"
        << "}";
    
    return oss.str();
}

std::string HttpServer::handlePumpaStatus() {
    if (!controller) {
        return "{\"error\": \"Controller nije dostupan\"}";
    }
    
    auto data = controller->getPumpData();
    
    std::ostringstream oss;
    oss << "{"
        << "\"aktivna\": " << (data.active ? "true" : "false") << ", "
        << "\"baterija\": " << data.battery << ", "
        << "\"greska\": null"
        << "}";
    
    return oss.str();
}

std::string HttpServer::handleGrijacStatus() {
    if (!controller) {
        return "{\"error\": \"Controller nije dostupan\"}";
    }
    
    auto data = controller->getHeaterData();
    
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(1);
    oss << "{"
        << "\"aktivan\": " << (data.active ? "true" : "false") << ", "
        << "\"temperatura\": " << data.temperature << ", "
        << "\"baterija\": " << data.battery << ", "
        << "\"greska\": null"
        << "}";
    
    return oss.str();
}

std::string HttpServer::handleErrors() {
    if (!controller) {
        return "{\"error\": \"Controller nije dostupan\"}";
    }
    
    auto errors = controller->getErrors();
    
    std::ostringstream oss;
    oss << "[";
    
    bool first = true;
    for (const auto& error : errors) {
        if (!first) {
            oss << ", ";
        }
        first = false;
        
        oss << "{"
            << "\"uredjaj\": \"" << error.device << "\", "
            << "\"tip\": \"" << error.type << "\", "
            << "\"vreme\": \"" << error.timestamp << "\""
            << "}";
    }
    
    oss << "]";
    
    return oss.str();
}
