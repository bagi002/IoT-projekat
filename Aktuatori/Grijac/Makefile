# Compiler and flags
CXX = g++
CXXFLAGS = -Wall -Wextra -std=c++11
LDFLAGS = -lmosquitto

# Target executable
TARGET = grejac

# Source files
SOURCES = main.cpp MQTT/mqtt.cpp Parse/parse.cpp ../common/file_mutex.cpp

# Object files
OBJECTS = $(SOURCES:.cpp=.o)

# Default target
all: $(TARGET)

# Build the executable
$(TARGET): $(OBJECTS)
	$(CXX) $(OBJECTS) -o $(TARGET) $(LDFLAGS)

# Build object files
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build files
clean:
	rm -f $(OBJECTS) $(TARGET)

# Rebuild everything
rebuild: clean all

# Phony targets
.PHONY: all clean rebuild
