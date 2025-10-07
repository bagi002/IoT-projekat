# 🚀 IoT Sistem - Automatsko Pokretanje

## 📋 Pregled

Ovaj skript automatski pokreće ceo IoT sistem organizovan po virtualnim ekranima koristeći `tmux`.

## 🖥️ Organizacija Ekrana

### Ekran 1: Simulacija
- **Komponenta**: `simulacija/simulation.py`
- **Funkcija**: Simulira vremenske uslove i ažurira `SimData/time.json`

### Ekran 2: Senzori i Aktuatori (Grid 2x2)
```
┌─────────────────┬─────────────────┐
│  Beton Senzor   │  Pumpa Aktuator │
│  (make)         │  (make)         │
├─────────────────┼─────────────────┤
│ Vazduh Senzor   │ Grijač Aktuator │
│  (make)         │  (make)         │
└─────────────────┴─────────────────┘
```

### Ekran 3: Kontroler i Aplikacija
```
┌─────────────────┬─────────────────┐
│   Kontroler     │  Web Aplikacija │
│   (make)        │ (start_app.sh)  │
└─────────────────┴─────────────────┘
```

## 🎮 Komande

### Pokretanje
```bash
./start_iot_system.sh
```

### Zaustavljanje
```bash
./stop_iot_system.sh
```

### Ručno upravljanje tmux sesijom
```bash
# Priključi se na sesiju
tmux attach -t iot_system

# Prebaci između ekrana
Ctrl+b + 0  # Simulacija
Ctrl+b + 1  # Senzori/Aktuatori  
Ctrl+b + 2  # Kontroler/Aplikacija

# Navigacija između panela na istom ekranu
Ctrl+b + strelice
Ctrl+b + q + broj_panela

# Izađi iz sesije (bez gašenja)
Ctrl+b + d

# Ubij sesiju
tmux kill-session -t iot_system
```

## 🌐 Web Interfejsi

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:5000
- **Kontroler**: http://localhost:3000

## 📦 Zavisnosti

Potrebno je da imate instalirane:
- `tmux`: `sudo apt install tmux`
- `make`: `sudo apt install build-essential`
- `python3`: System default
- `node.js`: Za neki od servisa (ako je potrebno)

## 🔧 Troubleshooting

### Problem: tmux nije instaliran
```bash
sudo apt update
sudo apt install tmux
```

### Problem: Neki Makefile ne radi
Proverite da li su svi direktorijumi ispravni i da li Makefile postoji:
```bash
ls -la Senzori/*/Makefile
ls -la Aktuatori/*/Makefile  
ls -la Kontroler/Makefile
```

### Problem: Portovi su zauzeti
Zaustavite postojeće procese:
```bash
sudo pkill -f "python.*5000"
sudo pkill -f "node.*3000" 
./stop_iot_system.sh
```

## 📝 Logovanje

Svaki terminal u tmux sesiji čuva svoj izlaz. Da vidite šta se dešava:
1. Priključite se: `tmux attach -t iot_system`
2. Idite na željeni ekran: `Ctrl+b + [0,1,2]`
3. Skrolujte kroz istoriju: `Ctrl+b + PgUp/PgDn`

## 🏁 Redosled Pokretanja

1. ✅ **Simulacija** (prvi) - generiše simulirane podatke
2. ✅ **Senzori** - čitaju simulirane podatke  
3. ✅ **Aktuatori** - reaguju na komande
4. ✅ **Kontroler** - koordiniše senzore i aktuatore
5. ✅ **Aplikacija** - pruža web interfejs

Skript automatski čeka između koraka da se svaka komponenta pokrene.