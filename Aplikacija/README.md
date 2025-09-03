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

### Backend (Flask)

1. Navigiraj u backend folder:
```bash
cd Aplikacija/backend
```

2. Instaliraj dependencije:
```bash
pip install -r requirements.txt
```

3. Pokreni Flask aplikaciju:
```bash
python app.py
```

Backend će biti dostupan na: `http://localhost:5000`

### Frontend

1. Navigiraj u frontend folder:
```bash
cd Aplikacija/frontend
```

2. Otvori `index.html` u web browseru ili pokreni lokalni web server:
```bash
# Sa Python
python -m http.server 8080

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
- **Styling**: Custom CSS sa modernim dizajnom

## Karakteristike

- Responsive dizajn
- Realtime ažuriranje podataka
- Moderna UI sa glassmorphism efektima
- Animacije i prelazi
- Toast notifikacije
- Grafički prikaz istorijskih podataka
