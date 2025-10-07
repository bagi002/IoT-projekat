#ifndef HTTPSERVER_H
#define HTTPSERVER_H

#include <microhttpd.h>
#include <string>
#include <functional>
#include <map>

// Forward declaration
class SystemController;

class HttpServer {
private:
    struct MHD_Daemon* daemon;
    int port;
    SystemController* controller;
    
    // Static callback koji MHD poziva za svaki HTTP zahtev
    static MHD_Result handleRequest(void* cls, struct MHD_Connection* connection,
                                   const char* url, const char* method,
                                   const char* version, const char* upload_data,
                                   size_t* upload_data_size, void** con_cls);
    
    // Pomoćne metode za kreiranje HTTP odgovora
    MHD_Response* createJsonResponse(const std::string& json, int status_code);
    MHD_Result sendResponse(struct MHD_Connection* connection, const std::string& json, int status_code);
    
    // Metode za obradu različitih API endpoint-a
    std::string handleBetonSensor();
    std::string handlePovrsinaSensor();
    std::string handlePumpaStatus();
    std::string handleGrijacStatus();
    std::string handleErrors();
    
public:
    HttpServer(int port = 3000);
    ~HttpServer();
    
    bool start(SystemController* ctrl);
    void stop();
    bool isRunning() const;
};

#endif // HTTPSERVER_H
