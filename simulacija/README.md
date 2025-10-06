# Simulacija Betonske Deke - IoT Projekat

Ova aplikacija simulira betonsku deku sa senzorima i aktuatorima u IoT sistemu.

## Struktura Projekta

```
simulacija/
├── simulation.py              # Glavna aplikacija sa GUI
├── run_simulation.py         # Pokretanje aplikacije
├── create_sample_commands.py # Kreiranje primera komandi
├── models/                   # Modeli simulacije
│   ├── __init__.py
│   ├── battery_model.py      # Model baterija
│   ├── concrete_model.py     # Model betona
│   ├── air_model.py         # Model vazduha
│   └── actuator_model.py    # Model aktuatora
└── utils/                   # Pomoćne klase
    ├── __init__.py
    ├── json_manager.py      # Upravljanje JSON fajlovima
    └── simulation_time.py   # Simulaciono vreme
```

## SimData Direktorijum

Aplikacija kreira `SimData` direktorijum sa sledećim JSON fajlovima:

- **time.json** - Datum i vreme simulacije (odvojena polja)
- **BETON.JSON** - Temperatura, vlažnost betona i baterija senzora
- **VAZDUH.JSON** - Temperatura, vlažnost vazduha i baterija senzora  
- **BATERIJE.JSON** - Nivoi baterija aktuatora
- **AKTUATORI.JSON** - Komande za pumpu i grijač (ULAZ u simulaciju)

### Format time.json

```json
{
  "date": "2025-05-05",
  "time": "12:00:00", 
  "step_minutes": 10
}
```

## Pokretanje

1. Pokretanje simulacije:
```bash
cd simulacija
python run_simulation.py
```

2. Kreiranje primera komandi za aktuatore:
```bash
python create_sample_commands.py
```

## Funkcionalnosti

### Simulacioni Modeli

1. **Betonska Deka**
   - Početna vlažnost: ~90%
   - Postupno sušenje sa fizičkim zavisnostima
   - Uticaj spoljnih faktora (temperatura, vlažnost)
   - Interakcija sa aktuatorima

2. **Mikro Klima Vazduha**
   - Dnevni ciklus temperature i vlažnosti
   - Interakcija sa betonom
   - Uticaj pumpe na cirkulaciju

3. **Baterije (4 komada)**
   - Senzor betona (indeks 0)
   - Senzor vazduha (indeks 1) 
   - Pumpa (indeks 2)
   - Grijač (indeks 3)
   - Normalan pad: 1% na 2h
   - Loš režim: 4% na sat
   - Mogućnost trenutnog "ubijanja"

4. **Aktuatori**
   - **Pumpa**: ON/OFF + vreme rada, hladi i povećava vlažnost
   - **Grijač**: ON/OFF + ciljna temperatura, grije vodu

### GUI Kontrole

- **Vreme**: Prikaz trenutnog vremena, korak simulacije
- **Pokretanje**: Start/Stop kontinuirane simulacije, jedan korak, restart
- **Spoljni uslovi**: Bazne vrednosti za podne (12:00) - temperature i vlažnosti
- **Baterije**: Označavanje loših baterija, ubijanje baterija
- **Status tabovi**: Prikaz stanja betona, vazduha, baterija, aktuatora

### Bazne Vrednosti i Dnevni Ciklus

Temperatura i vlažnost koje unesete u GUI se tretiraju kao **bazne vrednosti za podne (12:00)**:

- **24-satni Temperaturni Ciklus**: 
  - Koristi cosinusoidalnu funkciju: `bazna ± 8°C * cos(2π * (sat-12)/24)`
  - Maksimum: 12:00 podne (bazna + 8°C)
  - Minimum: 00:00 ponoć (bazna - 8°C)
  
- **24-satni Ciklus Vlažnosti** (obrnuto od temperature):
  - Formula: `bazna ± 25% * cos(2π * (sat-12)/24)` (obrnuto)
  - Minimum: 12:00 podne (bazna - 25%)
  - Maksimum: 00:00 ponoć (bazna + 25%)

### Sistem Sušenja Betonske Deke

Implementiran je realistični sistem sušenja deke tokom **7 dana**:

- **Početno stanje**: 100% vlažnosti (vreme izljevanja)
- **Finalno stanje**: 25% vlažnosti (nakon 7 dana)
- **Eksponencijalna kriva**: Brže sušenje na početku, sporije na kraju
- **Formula brzine**: `2.5% * e^(-2*dani/7) * faktor_vlažnosti`

### JSON Format Komandi (AKTUATORI.JSON)

```json
{
  "pump": {
    "status": 1,
    "runtime_minutes": 30
  },
  "heater": {
    "status": 1,
    "temperature": 35.0
  }
}
```

## Fizička Simulacija

### Formule i Zavisnosti

1. **Sušenje Betonske Deke** (novo - 7-dnevni sistem)
   - Početna vlažnost: 100% (izljevanje)
   - Finalna vlažnost: 25% (nakon 7 dana)
   - Eksponencijalna brzina sušenja: 2.5% * e^(-2*dani/7)
   - Uticaj temperature: viša temperatura = brže sušenje
   - Uticaj pumpe: povećava vlažnost (sporava sušenje)
   - Uticaj grijača: ubrzava sušenje

2. **Temperaturne Promene** (poboljšano)
   - 24-satni ciklus: cosinusoidalna funkcija
   - Bazna vrednost u podne ±8°C tokom dana
   - Termalna masa betona: sporije promene
   - Spoljni uticaj: postupno izjednačavanje

3. **Interakcija Vazduh-Beton** (reimplementirano)
   - Temperaturni transfer: zavisi od razlike temperatura
   - Transfer vlažnosti: zavisi od razlike vlažnosti i temperature
   - Intenzitet prenosa: proporcionalan razlikama
   - Beton oslobađa vlažnost u vazduh (realistično)

4. **Baterije**
   - Linearno pražnjenje sa različitim brzinama
   - Dodatna potrošnja za aktivne aktuatore
   - Funkcionalna ograničenja pri niskim nivoima

## Prilagođavanje Simulacije

### Lako Menjanje Parametara

Svi ključni parametri su izdvojeni kao konstante u klasama:

- `ConcreteModel`: brzine sušenja, termalna masa
- `AirModel`: dnevne varijacije, brzine razmene
- `BatteryManager`: brzine pražnjenja
- `ActuatorModel`: efikasnosti, kapaciteti

### Proširivanje

Modularni dizajn omogućava lako dodavanje:
- Novih senzora/aktuatora
- Spoljnih uticaja (kiša, vetar)
- Složenijih fizičkih modela
- Dodatnih GUI kontrola

## Vreme Simulacije

- Početno vreme: 5.5.2025 12:00
- Korak: konfigurabilan (default 10 minuta)
- Maksimalna simulacija: 7 dana
- Kontinuirana ili korak-po-korak

## Napomene

1. Simulacija čuva stanje u JSON fajlovima nakon svakog koraka
2. GUI se ažurira u realnom vremenu
3. Baterije utiču na funkcionalnost senzora/aktuatora
4. Fizički modeli su aproksimacije realnih procesa
5. Parametri se mogu lako menjati u kodu bez menjanja strukture