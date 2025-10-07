#!/bin/bash

# IoT System Shutdown Script
# Bezbedno zaustavlja ceo IoT sistem

echo "🛑 Zaustavljanje IoT sistema..."

# Proveri da li tmux sesija postoji
if ! tmux has-session -t iot_system 2>/dev/null; then
    echo "ℹ️  tmux sesija 'iot_system' ne postoji ili već je ugašena."
    exit 0
fi

echo "🔌 Zatvaranje tmux sesije 'iot_system'..."

# Pošalji Ctrl+C svim panelima da zaustavi procese
echo "⏹️  Šalje Ctrl+C svim komponentama..."

# Simulacija
tmux send-keys -t iot_system:Simulacija C-c 2>/dev/null

# Senzori i Aktuatori (4 panela)
tmux send-keys -t iot_system:Senzori_Aktuatori.0 C-c 2>/dev/null  # Beton senzor
tmux send-keys -t iot_system:Senzori_Aktuatori.1 C-c 2>/dev/null  # Vazduh senzor  
tmux send-keys -t iot_system:Senzori_Aktuatori.2 C-c 2>/dev/null  # Pumpa
tmux send-keys -t iot_system:Senzori_Aktuatori.3 C-c 2>/dev/null  # Grijač

# Kontroler i Aplikacija
tmux send-keys -t iot_system:Kontroler_Aplikacija.0 C-c 2>/dev/null  # Kontroler
tmux send-keys -t iot_system:Kontroler_Aplikacija.1 C-c 2>/dev/null  # Aplikacija

echo "⏳ Čekam 3 sekunde da se procesi zaustave..."
sleep 3

# Ubij tmux sesiju
tmux kill-session -t iot_system 2>/dev/null

# Zaustavi MQTT broker
echo "🔌 Zaustavljam MQTT broker..."
if pgrep -x "mosquitto" > /dev/null; then
    pkill mosquitto
    if [ $? -eq 0 ]; then
        echo "✅ MQTT broker je uspešno zaustavljen"
    else
        echo "⚠️  Možda je potrebno ručno zaustaviti MQTT broker"
    fi
else
    echo "ℹ️  MQTT broker nije bio pokrenut"
fi

echo "✅ IoT sistem je uspešno zaustavljen!"
echo ""
echo "💡 Da pokrenete sistem ponovo:"
echo "   ./start_iot_system.sh"
echo ""