#!/bin/bash

# IoT Sistem za Nadzor Betona - Stop Script
# Zaustavlja sve procese povezane sa aplikacijom

# Boje za terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo -e "${BLUE}Zaustavljanje IoT Sistem za Nadzor Betona...${NC}"

# Zaustavljanje procesa na portovima 5000 i 8080
print_step "Zaustavljanje backend servera (port 5000)..."
if lsof -ti:5000 >/dev/null 2>&1; then
    fuser -k 5000/tcp
    print_status "Backend server zaustavljen"
else
    print_status "Backend server nije bio aktivan"
fi

print_step "Zaustavljanje frontend servera (port 8080)..."
if lsof -ti:8080 >/dev/null 2>&1; then
    fuser -k 8080/tcp
    print_status "Frontend server zaustavljen"
else
    print_status "Frontend server nije bio aktivan"
fi

# Zaustavljanje Python procesa povezanih sa Flask aplikacijom
print_step "Zaustavljanje Flask procesa..."
pkill -f "python.*app.py" 2>/dev/null && print_status "Flask procesi zaustavljeni"

# Zaustavljanje HTTP servera
print_step "Zaustavljanje HTTP servera..."
pkill -f "python.*http.server" 2>/dev/null && print_status "HTTP server procesi zaustavljeni"

echo -e "${GREEN}Svi serveri su uspješno zaustavljeni!${NC}"
