# IoT Sistem za Nadzor Betona

Sistem za monitoring i kontrolu procesa očvršćavanja betona sa senzorima temperature i vlažnosti, kao i aktuatorima (pumpa za vodu i grijač).

## Struktura Projekta

```
Aplikacija/
├── backend/
│   ├── app.py              # Flask backend aplikacija
│   ├── requirements.txt    # Python dependencije
│   └── iot_data.db        # SQLite baza podataka (generisana automatski)
└── frontend/
    ├── index.html         # Glavna HTML stranica
    ├── style.css          # CSS stilovi
    └── script.js          # JavaScript funkcionalnost
```

## Pokretanje Aplikacije

### 🚀 Automatsko Pokretanje (Preporučeno)

Koristite našu naprednu startup skriptu koja automatski:
- Proverava Python instalaciju
- Kreira i aktivira virtualno okruženje
- Instalira sve dependencije
- Pokreće backend i frontend servere
- Otvara aplikaciju u browser-u

```bash
cd Aplikacija
./start_app.sh
```

### 🛑 Zaustavljanje Aplikacije

```bash
cd Aplikacija
./stop_app.sh
```

### 📝 Manuelno Pokretanje

#### Backend (Flask)

1. Navigiraj u backend folder:
```bash
cd Aplikacija/backend
```

2. Aktiviraj virtualno okruženje:
```bash
source ../.venv/bin/activate
```

3. Instaliraj dependencije:
```bash
pip install -r requirements.txt
```

4. Pokreni Flask aplikaciju:
```bash
python app.py
```

Backend će biti dostupan na: `http://localhost:5000`

#### Frontend

1. Navigiraj u frontend folder:
```bash
cd Aplikacija/frontend
```

2. Otvori `index.html` u web browseru ili pokreni lokalni web server:
```bash
# Sa Python
python3 -m http.server 8080

# Sa Node.js (ako imaš npx)
npx serve .
```

Frontend će biti dostupan na: `http://localhost:8080`

## Funkcionalnosti

### Dashboard
- **4 kartice** sa prikazom stanja uređaja:
  - Senzor betona (temperatura, vlažnost, baterija, status)
  - Senzor vazduha (temperatura, vlažnost, baterija, status)
  - Pumpa za vodu (status, baterija, preostalo vreme)
  - Grijač vode (status, baterija, temperatura)

### Manuelno Upravljanje
- Kontrola pumpe (pokretanje/zaustavljanje sa zadatim trajanjem)
- Kontrola grijača (pokretanje/zaustavljanje sa ciljnom temperaturom)

### Istorija
- Grafički prikaz temperatire i vlažnosti
- Mogućnost izbora vremenskog perioda (5h, 10h, 24h, 7 dana, svi podaci)
- Dva odvojena grafikona: temperatura i vlažnost

### Notifikacije
- Sistem notifikacija sa tri nivoa: kritično, upozorenje, info
- Toast notifikacije koje se pojavljuju na ekranu
- Lista svih notifikacija sa mogućnošću potvrđivanja

## API Endpoints

### Senzori
- `GET /api/dashboard` - Svi podaci za dashboard
- `GET /api/senzori/beton` - Podaci senzora betona
- `GET /api/senzori/vazduh` - Podaci senzora vazduha

### Aktuatori
- `GET /api/pumpa/stanje` - Status pumpe
- `GET /api/grijac/stanje` - Status grijača
- `POST /api/pumpa/upravljanje` - Kontrola pumpe
- `POST /api/grijac/upravljanje` - Kontrola grijača

### Istorija i Notifikacije
- `GET /api/istorija?hours=24` - Istorijski podaci
- `GET /api/notifikacije` - Lista notifikacija
- `POST /api/notifikacije/{id}/acknowledge` - Potvrdi notifikaciju

## Simulacija

Sistem koristi simulaciju umesto realnih uređaja:
- Automatsko generisanje realističnih podataka
- Simulacija promene temperature i vlažnosti
- Simulacija rada aktuatora
- Automatsko generisanje alarma i notifikacija

## Tehnologije

- **Backend**: Python Flask, SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Grafikoni**: Chart.js
- **Ikone**: Font Awesome
- **Styling**: Custom CSS sa futurističkim glassmorphism dizajnom
- **Automatizacija**: Bash skripta za potpuno automatsko pokretanje

## Karakteristike

- Responsive dizajn za sve uređaje
- Realtime ažuriranje podataka svakih 5 sekundi
- Futuristička UI sa glassmorphism efektima i neon bojama
- Animacije i smooth prelazi
- Toast notifikacije sa različitim nivoima upozorenja
- Grafički prikaz istorijskih podataka sa Chart.js
- Potpuno automatska startup skripta
- Virtualno okruženje management
- Auto-start u web browser-u
- Graceful shutdown sa Ctrl+C

## 🎨 Dizajn Karakteristike

- **Tamna tema** sa futurističkim gradijentima
- **Glassmorphism efekti** sa blur pozadinama
- **Neon glow efekti** za status indikatore
- **Animirani elementi** (pulsiranje, shimmer efekti)
- **Moderni button hover efekti**
- **Responsive layout** za sve veličine ekrana
- **Custom scrollbar** styling
- **Battery level** animirani indikatori
