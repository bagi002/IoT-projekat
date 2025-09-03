#!/bin/bash

# IoT Sistem za Nadzor Betona - Startup Script
# Automatski pokreće backend i frontend aplikaciju

# Boje za terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# ASCII Art Logo
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║    ██╗ ██████╗ ████████╗    ███████╗██╗███████╗████████╗███████╗ ║"
echo "║    ██║██╔═══██╗╚══██╔══╝    ██╔════╝██║██╔════╝╚══██╔══╝██╔════╝ ║"
echo "║    ██║██║   ██║   ██║       ███████╗██║███████╗   ██║   █████╗   ║"
echo "║    ██║██║   ██║   ██║       ╚════██║██║╚════██║   ██║   ██╔══╝   ║"
echo "║    ██║╚██████╔╝   ██║       ███████║██║███████║   ██║   ███████╗ ║"
echo "║    ╚═╝ ╚═════╝    ╚═╝       ╚══════╝╚═╝╚══════╝   ╚═╝   ╚══════╝ ║"
echo "║                                                                  ║"
echo "║              SISTEM ZA NADZOR OČVRŠĆAVANJA BETONA               ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funkcija za ispis poruka
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Provjera da li smo u ispravnom direktoriju
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${WHITE}Projektni direktorij: ${PROJECT_DIR}${NC}"

# Provjera da li postoje potrebni folderi
if [ ! -d "$PROJECT_DIR/backend" ] || [ ! -d "$PROJECT_DIR/frontend" ]; then
    print_error "Nedostaju backend ili frontend folderi!"
    exit 1
fi

# Funkcija za čišćenje procesa pri izlasku
cleanup() {
    print_step "Zaustavljanje servera..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        print_status "Backend zaustavljen"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        print_status "Frontend zaustavljen"
    fi
    echo -e "${CYAN}Hvala što ste koristili IoT Sistem za Nadzor Betona!${NC}"
    exit 0
}

# Postavljanje trap signala za čišćenje
trap cleanup SIGINT SIGTERM

print_step "Pokretanje IoT Sistem za Nadzor Betona..."

# 1. Provjera Python instalacije
print_step "Provjera Python instalacije..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 nije instaliran!"
    exit 1
fi
print_status "Python3 je dostupan: $(python3 --version)"

# 2. Kreiranje virtualnog okruženja ako ne postoji
VENV_DIR="$PROJECT_DIR/../.venv"
if [ ! -d "$VENV_DIR" ]; then
    print_step "Kreiranje virtualnog okruženja..."
    python3 -m venv "$VENV_DIR"
    print_status "Virtualno okruženje kreirano"
else
    print_status "Virtualno okruženje već postoji"
fi

# 3. Aktivacija virtualnog okruženja
print_step "Aktivacija virtualnog okruženja..."
source "$VENV_DIR/bin/activate"
print_status "Virtualno okruženje aktivirano"

# 4. Instaliranje Python dependencija
print_step "Provjera i instalacija Python dependencija..."
cd "$PROJECT_DIR/backend"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_status "Python dependencije instalirane"
else
    print_warning "requirements.txt ne postoji, instaliram osnovne pakete..."
    pip install Flask Flask-CORS --quiet
fi

# 5. Provjera da li su portovi slobodni
print_step "Provjera dostupnosti portova..."

check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

if ! check_port 5000; then
    print_warning "Port 5000 je zauzet! Pokušavam da zaustavim postojeći proces..."
    fuser -k 5000/tcp 2>/dev/null
    sleep 2
fi

if ! check_port 8080; then
    print_warning "Port 8080 je zauzet! Pokušavam da zaustavim postojeći proces..."
    fuser -k 8080/tcp 2>/dev/null
    sleep 2
fi

# 6. Pokretanje backend servera
print_step "Pokretanje Flask backend servera..."
cd "$PROJECT_DIR/backend"
python app.py &
BACKEND_PID=$!

# Čekanje da se backend pokrene
sleep 3

# Provjera da li je backend uspješno pokrenut
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_status "Backend server pokrenut (PID: $BACKEND_PID)"
    print_status "Backend URL: http://localhost:5000"
else
    print_error "Greška pri pokretanju backend servera!"
    exit 1
fi

# 7. Pokretanje frontend servera
print_step "Pokretanje frontend servera..."
cd "$PROJECT_DIR/frontend"
python3 -m http.server 8080 &
FRONTEND_PID=$!

# Čekanje da se frontend pokrene
sleep 2

# Provjera da li je frontend uspješno pokrenut
if kill -0 $FRONTEND_PID 2>/dev/null; then
    print_status "Frontend server pokrenut (PID: $FRONTEND_PID)"
    print_status "Frontend URL: http://localhost:8080"
else
    print_error "Greška pri pokretanju frontend servera!"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 8. Uspješan startup
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                        SISTEM POKRENUT!                       ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}║  ${WHITE}Backend API:${NC}     ${CYAN}http://localhost:5000${NC}                     ${GREEN}║${NC}"
echo -e "${GREEN}║  ${WHITE}Frontend Web:${NC}    ${CYAN}http://localhost:8080${NC}                     ${GREEN}║${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}║  ${YELLOW}Pritisnite Ctrl+C za zaustavljanje${NC}                        ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 9. Pokušaj automatskog otvaranja web browser-a
print_step "Pokušaj otvaranja web aplikacije..."
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8080" 2>/dev/null &
    print_status "Web aplikacija otvorena u browser-u"
elif command -v open &> /dev/null; then
    open "http://localhost:8080" 2>/dev/null &
    print_status "Web aplikacija otvorena u browser-u"
else
    print_warning "Nije moguće automatski otvoriti browser. Idite na: http://localhost:8080"
fi

# 10. Prikaz log-a u realnom vremenu
echo -e "${BLUE}═══════════════════════ APLIKACIJSKI LOG ═══════════════════════${NC}"

# Čekanje na korisnikov input za izlaz
while true; do
    sleep 1
    # Provjera da li su procesi još uvek aktivni
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend proces je neočekivano zaustavljen!"
        cleanup
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend proces je neočekivano zaustavljen!"
        cleanup
    fi
done
