CC = g++
TARGET = senzor1
SOURCES = main.cpp Parse/parse.cpp MQTT/mqtt.cpp
LIBS = -lmosquitto

$(TARGET): $(SOURCES)
	$(CC) -o $(TARGET) $(SOURCES) $(LIBS)

clean:
	rm -f $(TARGET)

.PHONY: clean
