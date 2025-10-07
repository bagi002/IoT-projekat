#!/bin/bash

# IoT System Startup Script
# Pokreće ceo IoT sistem organizovan po virtualnim ekranima

PROJECT_ROOT="/home/bagi/Desktop/IoT projekat"

echo "🚀 Pokretanje IoT sistema..."
echo "📁 Project root: $PROJECT_ROOT"

# Proveri da li tmux postoji
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux nije instaliran. Instalirajte ga sa: sudo apt install tmux"
    exit 1
fi

# Proveri da li mosquitto postoji
if ! command -v mosquitto &> /dev/null; then
    echo "❌ mosquitto nije instaliran. Instalirajte ga sa: sudo apt install mosquitto mosquitto-clients"
    exit 1
fi

# Pokreni MQTT broker ako već nije pokrenut
echo "🔌 Proveravam MQTT broker..."
if ! pgrep -x "mosquitto" > /dev/null; then
    echo "▶️  Pokretam Mosquitto MQTT broker..."
    mosquitto -d -p 1883
    if [ $? -eq 0 ]; then
        echo "✅ MQTT broker je uspešno pokrenut na portu 1883"
    else
        echo "❌ Greška pri pokretanju MQTT brokera"
        exit 1
    fi
else
    echo "✅ MQTT broker je već pokrenut"
fi

# Funkcija za čekanje da se komponenta pokrene
wait_for_startup() {
    echo "⏳ Čekam $1 sekundi da se $2 pokrene..."
    sleep $1
}

# Ubij postojeće tmux sesije ako postoje
tmux has-session -t iot_system 2>/dev/null && tmux kill-session -t iot_system

echo "🖥️  Kreiram tmux sesiju: iot_system"

# EKRAN 1: SIMULACIJA
echo "🖥️  Ekran 1: Pokretanje simulacije..."
tmux new-session -d -s iot_system -n "Simulacija"
tmux send-keys -t iot_system:Simulacija "cd '$PROJECT_ROOT/simulacija'" Enter
tmux send-keys -t iot_system:Simulacija "clear" Enter
tmux send-keys -t iot_system:Simulacija "echo '🎮 SIMULACIJA - Virtuelni Ekran 1'" Enter
tmux send-keys -t iot_system:Simulacija "echo '▶️  Pokretam simulation.py...'" Enter
tmux send-keys -t iot_system:Simulacija "python3 simulation.py" Enter

wait_for_startup 3 "simulacija"

# EKRAN 2: SENZORI I AKTUATORI (4 terminala u grid layout)
echo "🖥️  Ekran 2: Pokretanje senzora i aktuatora..."
tmux new-window -t iot_system -n "Senzori_Aktuatori"

# Podeli ekran na 4 dela (2x2 grid)
tmux split-window -t iot_system:Senzori_Aktuatori -h   # Podeli horizontalno
tmux split-window -t iot_system:Senzori_Aktuatori.0 -v # Podeli levi deo vertikalno  
tmux split-window -t iot_system:Senzori_Aktuatori.2 -v # Podeli desni deo vertikalno

# Panel 0 (gore levo): Beton Senzor
tmux send-keys -t iot_system:Senzori_Aktuatori.0 "cd '$PROJECT_ROOT/Senzori/Beton'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.0 "clear" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.0 "echo '🌡️  BETON SENZOR - Panel 1/4'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.0 "echo '▶️  make...'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.0 "make" Enter

wait_for_startup 2 "beton senzor"

# Panel 1 (dole levo): Vazduh Senzor  
tmux send-keys -t iot_system:Senzori_Aktuatori.1 "cd '$PROJECT_ROOT/Senzori/Vazduh'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.1 "clear" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.1 "echo '🌬️  VAZDUH SENZOR - Panel 2/4'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.1 "echo '▶️  make...'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.1 "make" Enter

wait_for_startup 2 "vazduh senzor"

# Panel 2 (gore desno): Pumpa Aktuator
tmux send-keys -t iot_system:Senzori_Aktuatori.2 "cd '$PROJECT_ROOT/Aktuatori/Pumpa'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.2 "clear" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.2 "echo '💧 PUMPA AKTUATOR - Panel 3/4'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.2 "echo '▶️  make...'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.2 "make" Enter

wait_for_startup 2 "pumpa"

# Panel 3 (dole desno): Grijač Aktuator
tmux send-keys -t iot_system:Senzori_Aktuatori.3 "cd '$PROJECT_ROOT/Aktuatori/Grijac'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.3 "clear" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.3 "echo '🔥 GRIJAČ AKTUATOR - Panel 4/4'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.3 "echo '▶️  make...'" Enter
tmux send-keys -t iot_system:Senzori_Aktuatori.3 "make" Enter

wait_for_startup 3 "grijač"

# EKRAN 3: KONTROLER I APLIKACIJA (2 terminala)
echo "🖥️  Ekran 3: Pokretanje kontrolera i aplikacije..."
tmux new-window -t iot_system -n "Kontroler_Aplikacija"

# Podeli ekran na 2 dela
tmux split-window -t iot_system:Kontroler_Aplikacija -h

# Panel 0 (levo): Kontroler
tmux send-keys -t iot_system:Kontroler_Aplikacija.0 "cd '$PROJECT_ROOT/Kontroler'" Enter
tmux send-keys -t iot_system:Kontroler_Aplikacija.0 "clear" Enter
tmux send-keys -t iot_system:Kontroler_Aplikacija.0 "echo '🎛️  KONTROLER - Levi Panel'" Enter
tmux send-keys -t iot_system:Kontroler_Aplikacija.0 "echo '▶️  make...'" Enter
tmux send-keys -t iot_system:Kontroler_Aplikacija.0 "make" Enter

wait_for_startup 3 "kontroler"

# Panel 1 (desno): Aplikacija
tmux send-keys -t iot_system:Kontroler_Aplikacija.1 "cd '$PROJECT_ROOT/Aplikacija'" Enter
tmux send-keys -t iot_system:Kontroler_Aplikacija.1 "clear" Enter
tmux send-keys -t iot_system:Kontroler_Aplikacija.1 "echo '🌐 WEB APLIKACIJA - Desni Panel'" Enter
tmux send-keys -t iot_system:Kontroler_Aplikacija.1 "echo '▶️  ./start_app.sh...'" Enter
tmux send-keys -t iot_system:Kontroler_Aplikacija.1 "./start_app.sh" Enter

wait_for_startup 2 "aplikacija"

echo ""
echo "✅ IoT sistem je uspešno pokrenut!"
echo ""
echo "📺 TMUX SESIJA: iot_system"
echo "   🖥️  Ekran 1 (Simulacija):      tmux attach -t iot_system -c Simulacija"
echo "   🖥️  Ekran 2 (Senzori/Aktuatori): tmux attach -t iot_system -c Senzori_Aktuatori"  
echo "   🖥️  Ekran 3 (Kontroler/App):     tmux attach -t iot_system -c Kontroler_Aplikacija"
echo ""
echo "🎮 UPRAVLJANJE:"
echo "   Priključi se:  tmux attach -t iot_system"
echo "   Prebaci ekran: Ctrl+b + [0,1,2] ili Ctrl+b + n/p"
echo "   Izađi:         Ctrl+b + d (detach) ili exit u svakom terminalu"
echo "   Ubij sesiju:   tmux kill-session -t iot_system"
echo ""
echo "🌐 WEB INTERFEJS:"
echo "   Frontend: http://localhost:8080"
echo "   Backend:  http://localhost:5000"
echo ""

# Automatski se priključi na sesiju
echo "🔗 Priključujem se na tmux sesiju..."
sleep 2
tmux attach -t iot_system