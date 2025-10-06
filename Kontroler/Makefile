# Makefile za Kontroler

CXX = g++
CXXFLAGS = -std=c++11 -Wall -I.
LDFLAGS = -lmosquitto -lmicrohttpd -lpthread

TARGET = kontroler
SOURCES = main.cpp MQTT/mqtt.cpp MQTT/SystemController.cpp MQTT/HttpServer.cpp
OBJECTS = $(SOURCES:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CXX) $(OBJECTS) -o $(TARGET) $(LDFLAGS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run
