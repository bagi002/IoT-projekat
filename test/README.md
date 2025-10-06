# IoT Kontroler Simulator - Test App

## Opis
Ova aplikacija je mini test simulator koji emulira IoT kontroler. Omogućava vam da:

- 🔧 **Postavite stanja senzora i aktuatora** - temperatura, vlažnost, baterije, status
- 🚨 **Generirete greške** prema specifikaciji sistema 
- 📡 **Emulirate API endpoints** koje glavna aplikacija poziva
- 🧪 **Testirate batch scenarije** sa više grešaka odjednom

## Pokretanje

### 1. Instalirajte dependencies:
```bash
cd test
pip install -r requirements.txt
```

### 2. Pokrenite simulator:
```bash
python kontroler_simulator.py
```

### 3. Otvorite web interfejs:
Idite na: **http://localhost:3000**

## Funkcionalnosti

### 🎛️ Web kontrolni panel
- **Senzor betona**: temperatura, vlažnost, baterija
- **Senzor površine**: temperatura, vlažnost, baterija  
- **Pumpa**: aktivna/neaktivna, baterija
- **Grijač**: aktivan/neaktivan, temperatura, baterija

### 🚨 Generisanje grešaka
**Pojedinačne greške:**
- `niska_baterija` - baterija uređaja ispod 20%
- `niska_vlaznost` - vlažnost betona ispod ciljnih vrijednosti
- `visoka_temperatura` - temperatura betona iznad maksimalne dozvoljene
- `niska_temperatura` - temperatura betona ispod minimalne
- `greska_senzora` - greška u radu senzora
- `prekid_komunikacije` - gubitak konekcije sa uređajem
- `kritična_temperatura_grijaca` - grijač pregrijava
- `system_maintenance` - potrebno održavanje sistema

**Batch testovi:**
- **Niska baterija** - serija grešaka niskih baterija
- **Kritične temperature** - temperature van granica
- **Niska vlažnost** - problemi sa vlažnosću
- **Mešovite greške** - kombinacija različitih tipova

### 📡 API Endpoints

**Koje glavna aplikacija poziva:**
- `GET /api/senzori/beton` - stanje senzora betona
- `GET /api/senzori/povrsina` - stanje senzora površine  
- `GET /api/pumpa/stanje` - stanje pumpe
- `GET /api/grijac/stanje` - stanje grijača

**Kontrolni endpoints:**
- `POST /api/set_state` - postavlja nova stanja
- `POST /api/send_error` - šalje grešku glavnoj aplikaciji
- `POST /api/batch_errors` - šalje batch greške
- `GET /api/test_connection` - testira konekciju

## Kako koristiti

### 1. Pokrenite glavnu aplikaciju:
```bash
cd ../Aplikacija
python backend/app.py
```
Glavna aplikacija će biti na **http://localhost:5000**

### 2. Pokrenite simulator:
```bash
cd ../test  
python kontroler_simulator.py
```
Simulator će biti na **http://localhost:3000**

### 3. Testirajte povezanost:
- Otvorite simulator u browser-u
- Kliknite "Test konekcije" - treba da bude zeleno ✅
- Postavite nova stanja senzora
- Generisite greške i gledajte ih u glavnoj aplikaciji

## Primeri korišćenja

### Testiranje alarma za nisku vlažnost:
1. Postavite vlažnost betona na 30%
2. Generisite grešku "niska_vlaznost"
3. Proverite notifikaciju u glavnoj aplikaciji

### Testiranje kritične temperature:
1. Postavite temperaturu betona na 45°C
2. Generisite grešku "visoka_temperatura"  
3. Trebalo bi da vidite kritični alarm

### Batch testiranje:
1. Kliknite "Kritične temperature"
2. Sistem će poslati više grešaka odjednom
3. Proverite kako se sistem ponaša sa višestrukim alarmima

## Napomene

- Simulator radi na portu **3000**, glavna aplikacija na portu **5000**
- Automatski testira konekciju svakih 30 sekundi
- Poruke o uspešnosti/grešci se prikazuju 5 sekundi
- Sva stanja se čuvaju u memoriji (resetuju se pri restartovanju)

## Struktura fajlova

```
test/
├── kontroler_simulator.py    # Glavni Flask server
├── templates/
│   └── simulator.html       # Web interfejs
├── requirements.txt         # Python dependencies  
└── README.md               # Ova dokumentacija
```