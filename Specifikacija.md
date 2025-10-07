# Sistem za nadzor očvršćavanja betonske deke

## Uređaji u sistemu

### Kontroler (broker)
- Centralni uređaj koji upravlja sistemom

### Senzori (Temperatura i vlažnost)
- **Senzor temperature iznad površine betona**
- **Senzor temperature betona**
- **Senzor vlažnosti vazduha iznad betona**
- **Senzor vlažnosti betona**

### Aktuatori
- **Pumpa za vodu** - služi da aktivira prskalice za poljevanje betonske konstrukcije (pali se i radi fiksno zadato vrijeme t)
- **Grijač vode** - omogućava da se u zimskim uslovima pri poljevanju betona isti zagrije

---

## Ciljevi sistema

- Stabilno očvršćavanje betona u cilju da se spriječi pojava mikro pukotina
- Održavanje vlažnosti betona i vlažnosti vazduha na odgovarajućem nivou da se spriječi prebrzo očvršćavanje betona (bitan faktor u sistemu je vrijeme od izljevanja betona)
- Održavanje stabilne razlike između spoljne temperature i temperature betona

---

## Detaljni ciljevi zavisnosti mjerenih traženih veličina (Nacrt - primer)

### 🌡️ Temperaturna kontrola
- **U prvih 12 sata od izljevanja**: razlika ne smije prelaziti ±3°C
- **Poslije 12 do 24 sata**: razlika može biti ±5°C
- **Poslije 24h do 7 dana**: razlika može biti ±7°C
- **Minimalna temperatura betona**: 5°C
- **Maksimalna temperatura betona**: 35°C

### 💧 Kontrola vlažnosti
- **Prvi dan (0-12h)**: vlažnost betona >80%
- **Prvi dan (12-24h)**: vlažnost betona >60%
- **Drugi dan**: vlažnost betona >50%
- **Dan 2-3**: vlažnost betona >40%
- **Dan 3-7**: vlažnost betona >15%

### ⚙️ Aktivacija sistema
**Pumpa se aktivira ako:**
- vlažnost betona padne ispod ciljnih vrijednosti
- vlažnost vazduha je premala (ispod 50%) što utiče na isušivanje betona
- temperatura betona je iznad trazenih vrijednosti - poljevanje hladnom vodom

**Grijač se aktivira ako:**
- temperatura betona je ipod trazenih vrijednosti - poljevanje toplom vodom
- temperatura vazduha <10°C i treba poljevanje

**Ograničenja:**
- Sistem sprječava rad pumpe ako je temperatura vazduha <2°C
- Maksimalno trajanje kontinuiranog rada pumpe: 30 minuta
- Minimum pauze između aktivacija pumpe: 15 minuta
- Grijač + pumpa rade istovremeno kada je potrebno zagrijavanje vode za poljevanje

### 🚨 Alarmi i upozorenja
- **Kritično**: temperatura betona <0°C ili >40°C
- **Upozorenje**: vlažnost betona ispod ciljnih vrijednosti >2 sata
- **Upozorenje**: razlika temperatura >dozvoljenog raspona
- **Info**: niska baterija (<20%), greška senzora

---

## Struktura sistema

```
                            ┌─────────────────────┐
                            │     APLIKACIJA      │
                            │   (Centralni UI)    │
                            └──────────▲──────────┘
                                       │
                                       ▼
┌─────────────────┐        ┌─────────────────────┐        ┌─────────────────┐
│  Grijač vode    │<-------│     KONTROLER       │------->│   Pumpa za vodu │
│                 │        │      (Broker)       │        │                 │
└─────────────────┘        └──────────┬──────────┘        └─────────────────┘
                                      │
                            ┌─────────┴─────────┐
                            │                   │
                            ▲                   ▲
                            │                   │
                    ┌─────────────────┐ ┌─────────────────┐
                    │ Senzor temp.    │ │ Senzor temp.    │
                    │ iznad betona    │ │ betona          │
                    └─────────────────┘ └─────────────────┘
                            ▲                   ▲
                            │                   │
                    ┌─────────────────┐ ┌─────────────────┐
                    │ Senzor vlažnosti│ │ Senzor vlažnosti│
                    │ vazduha         │ │ betona          │
                    └─────────────────┘ └─────────────────┘
```

---

## Komunikacioni protokoli

### 📡 MQTT Protokol

| Tema                                    | Publisher             | Subscriber    |
|-----------------------------------------|-----------------------|---------------|
| ploca1/beton/temperatura                | Senzor u betonu       | Kontroler     |
| ploca1/beton/vlaznost                   | Senzor u betonu       | Kontroler     |
| ploca1/beton/baterija                   | Senzor u betonu       | Kontroler     |
| ploca1/povrsina/temperatura             | Senzor iznad betona   | Kontroler     |
| ploca1/povrsina/vlaznost                | Senzor iznad betona   | Kontroler     |
| ploca1/povrsina/baterija                | Senzor iznad betona   | Kontroler     |
| ploca1/vodena_pumpa/ventil/stanje       | Kontroler             | Pumpa za vodu |
| ploca1/vodena_pumpa/ventil/vreme_rada   | Kontroler             | Pumpa za vodu |
| ploca1/vodena_pumpa/baterija            | Pumpa za vodu         | Kontroler     |
| ploca1/grijac_vode/stanje               | Kontroler             | Grijač vode   |
| ploca1/grijac_vode/temperatura          | Kontroler             | Grijač vode   |
| ploca1/grijac_vode/baterija             | Grijač vode           | Kontroler     |

### 🌐 HTTP Protokol (Kontroler ↔ Aplikacija)

#### GET zahtevi - Čitanje podataka

**Senzori:**
- `GET /api/senzori/beton`  
  Odgovor: `{"temperatura": 25.5, "vlaznost": 65.2, "baterija": 85, "greska": null}`

- `GET /api/senzori/povrsina`  
  Odgovor: `{"temperatura": 22.1, "vlaznost": 58.7, "baterija": 92, "greska": null}`

**Aktuatori:**
- `GET /api/pumpa/stanje`  
  Odgovor: `{"aktivna": true, "baterija": 78, "greska": null}`

- `GET /api/grijac/stanje`  
  Odgovor: `{"aktivan": false, "temperatura": 45.2, "baterija": 65, "greska": null}`

#### Greške i upozorenja
- `GET /api/greske`  
  Odgovor: `[{"uredjaj": "pumpa", "tip": "niska_baterija", "vreme": "2024-01-15T10:30:00Z"}]`
  ## Pokriti vise gresaka jos par ali svaka ima isti json obrazac uredjaj koji je triger , naziv tip greske - upozorenja 
  i vremme
  pokriti na primer: niska vlaznost, pad temeprature vazduha u minus i sl ...



---

## 📱 Specifikacija aplikacije

### 🏠 Dashboard - Glavni pregled
- **Kartica "Senzor betona"**: temperatura, vlažnost, baterija %, status (online/offline)
- **Kartica "Senzor vazduha"**: temperatura, vlažnost, baterija %, status (online/offline)
- **Kartica "Pumpa"**: status (radi/ne radi), baterija %, preostalo vrijeme rada
- **Kartica "Grijač"**: status (radi/ne radi), baterija %, trenutna temperatura
- **Vrijeme od izljevanja betona**: (dani:sati:minuti)

### 🎛️ Manuelno upravljanje
- **"POKRENI PUMPU"** dugme + polje za unos sekundi (default 300)
- **"ZAUSTAVI PUMPU"** dugme
- **"POKRENI GRIJAČ"** dugme
- **"ZAUSTAVI GRIJAČ"** dugme
- **"Automatski režim ON/OFF"** prekidač

### 🚨 Alarmi i notifikacije
- Lista alarma sa bojama (crveno-kritično, žuto-upozorenje, plavo-info)
- Polja: vrijeme, tip alarma, opis, status
- Dugme "Potvrdi alarm" za svaki red
- SMS broj za slanje kritičnih alarma

### 📊 Grafikoni
- **Grafik 1**: Temperatura betona i vazduha (zadnjih 24h)
- **Grafik 2**: Vlažnost betona (zadnjih 24h)
- Jednostavni linijski grafikoni sa legendom

---

## 🖥️ Simulacija sistema

### 💻 Simulirano okruženje
- Sistem će biti implementiran u simuliranom okruženju umjesto sa realnim hardverom
- Svi senzori će biti simulirani softverski sa realističnim vrijednostima
- Aktuatori (pumpa i grijač) će biti simulirani sa vizuelnim indikatorima
- Simulacija uključuje varijacije temperatura i vlažnosti tokom dana
- Ukljucuje mogucnost pokretanja niza mikro testova koje kreiraju odredjeni okidac
  a u cilju da se vidi kako se sistem ponasa u odnosu na dati dogadjaj


### ⚙️ Simulacijski parametri
- **Temperatura vazduha**: 5°C do 35°C (dnevne varijacije)
- **Temperatura betona**: bazirana na temperaturi vazduha ± simulirane razlike
- **Vlažnost betona**: simulirano opadanje prema vremenskim periodima
- **Vlažnost vazduha**: 30% do 90% (ovisno o vremenskim uslovima)
- **Baterije**: simulirano pražnjenje tokom vremena (1-2% dnevno)

### 🔧 Simulacija grešaka
- Nasumične greške senzora (5% vjerovatnoća)
- Simulacija slabih baterija
- Simulacija prekida komunikacije
- Testiranje alarma i notifikacija

### ✅ Prednosti simulacije
- Brže testiranje različitih scenarija
- Sigurno testiranje kritičnih situacija
- Ponovljivost eksperimenata
- Lakše demonstriranje funkcionalnosti sistema
