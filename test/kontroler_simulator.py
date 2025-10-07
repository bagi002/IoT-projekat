#!/usr/bin/env python3
"""
IoT Kontroler Simulator - Test App
Emulira kontroler koji može da postavlja stanja senzora i generiše greške
"""

from flask import Flask, render_template, request, jsonify
import requests
import json
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Trenutna stanja uređaja
current_state = {
    'senzori': {
        'beton': {
            'temperatura': 22.5,
            'vlaznost': 65.0,
            'baterija': 85,
            'greska': None
        },
        'povrsina': {
            'temperatura': 20.0,
            'vlaznost': 55.0,
            'baterija': 92,
            'greska': None
        }
    },
    'aktuatori': {
        'pumpa': {
            'aktivna': False,
            'baterija': 78,
            'greska': None
        },
        'grijac': {
            'aktivan': False,
            'temperatura': 25.0,
            'baterija': 65,
            'greska': None
        }
    }
}

# URL glavne aplikacije
MAIN_APP_URL = 'http://localhost:5000'

@app.route('/')
def index():
    """Glavna stranica za kontrolu simulatora"""
    return render_template('simulator.html', state=current_state)

@app.route('/api/set_state', methods=['POST'])
def set_state():
    """Postavlja nova stanja uređaja"""
    try:
        data = request.json
        
        # Ažuriramo stanje
        if 'senzori' in data:
            for senzor, values in data['senzori'].items():
                if senzor in current_state['senzori']:
                    current_state['senzori'][senzor].update(values)
        
        if 'aktuatori' in data:
            for aktuator, values in data['aktuatori'].items():
                if aktuator in current_state['aktuatori']:
                    current_state['aktuatori'][aktuator].update(values)
        
        return jsonify({'success': True, 'message': 'Stanje ažurirano'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/send_error', methods=['POST'])
def send_error():
    """Šalje grešku glavnoj aplikaciji"""
    try:
        data = request.json
        uredjaj = data.get('uredjaj')
        tip = data.get('tip')
        poruka = data.get('poruka', f'{tip} na uređaju {uredjaj}')
        
        # Formatiramo grešku prema specifikaciji
        error_data = {
            'uredjaj': uredjaj,
            'tip': tip,
            'poruka': poruka,
            'vreme': datetime.now().isoformat() + 'Z'
        }
        
        # Šaljemo grešku glavnoj aplikaciji
        response = requests.post(f'{MAIN_APP_URL}/api/greska', 
                               json=error_data,
                               timeout=5)
        
        if response.status_code == 200:
            return jsonify({
                'success': True, 
                'message': f'Greška "{tip}" poslana za uređaj "{uredjaj}"',
                'response': response.json()
            })
        else:
            return jsonify({
                'success': False, 
                'error': f'Glavna aplikacija vratila status {response.status_code}'
            }), 400
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False, 
            'error': 'Ne mogu da se povezem sa glavnom aplikacijom. Da li je pokrenuta na portu 5000?'
        }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/batch_errors', methods=['POST'])
def send_batch_errors():
    """Šalje više grešaka odjednom za testiranje"""
    try:
        batch_type = request.json.get('type', 'mixed')
        
        errors_to_send = []
        
        if batch_type == 'low_battery':
            # Serija grešaka niske baterije
            errors_to_send = [
                {'uredjaj': 'beton_senzor', 'tip': 'niska_baterija', 'poruka': 'Baterija senzora betona na 15%'},
                {'uredjaj': 'povrsina_senzor', 'tip': 'niska_baterija', 'poruka': 'Baterija senzora površine na 18%'},
                {'uredjaj': 'pumpa', 'tip': 'niska_baterija', 'poruka': 'Baterija pumpe na 12%'},
            ]
        elif batch_type == 'temperature_critical':
            # Kritične temperature
            errors_to_send = [
                {'uredjaj': 'beton_senzor', 'tip': 'visoka_temperatura', 'poruka': 'Temperatura betona 42°C - KRITIČNO!'},
                {'uredjaj': 'grijac', 'tip': 'kritična_temperatura_grijaca', 'poruka': 'Grijač pregrijava - 85°C!'},
            ]
        elif batch_type == 'humidity_low':
            # Niska vlažnost
            errors_to_send = [
                {'uredjaj': 'beton_senzor', 'tip': 'niska_vlaznost', 'poruka': 'Vlažnost betona 35% - ispod ciljne vrednosti'},
                {'uredjaj': 'povrsina_senzor', 'tip': 'niska_vlaznost', 'poruka': 'Vlažnost vazduha 25% - presuvo'},
            ]
        else:  # mixed
            # Mešovite greške
            errors_to_send = [
                {'uredjaj': 'beton_senzor', 'tip': 'greska_senzora', 'poruka': 'Nepravilni podaci - moguća greška senzora'},
                {'uredjaj': 'pumpa', 'tip': 'prekid_komunikacije', 'poruka': 'Gubitak komunikacije sa pumpom'},
                {'uredjaj': 'sistem', 'tip': 'system_maintenance', 'poruka': 'Potrebno održavanje sistema - 30 dana bez servisa'},
                {'uredjaj': 'povrsina_senzor', 'tip': 'niska_temperatura', 'poruka': 'Temperatura vazduha -2°C'},
            ]
        
        results = []
        for error in errors_to_send:
            try:
                error['vreme'] = datetime.now().isoformat() + 'Z'
                response = requests.post(f'{MAIN_APP_URL}/api/greska', 
                                       json=error,
                                       timeout=5)
                results.append({
                    'error': error,
                    'success': response.status_code == 200,
                    'status_code': response.status_code
                })
                time.sleep(0.5)  # Kratka pauza između slanja
            except Exception as e:
                results.append({
                    'error': error,
                    'success': False,
                    'error_msg': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'Poslano {len(errors_to_send)} grešaka tipa "{batch_type}"',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# API endpoints koje glavna aplikacija poziva
@app.route('/api/senzori/beton', methods=['GET'])
def get_beton_senzor():
    """Vraća stanje senzora betona"""
    return jsonify(current_state['senzori']['beton'])

@app.route('/api/senzori/povrsina', methods=['GET'])
def get_povrsina_senzor():
    """Vraća stanje senzora površine"""
    return jsonify(current_state['senzori']['povrsina'])

@app.route('/api/pumpa/stanje', methods=['GET'])
def get_pumpa_stanje():
    """Vraća stanje pumpe"""
    return jsonify(current_state['aktuatori']['pumpa'])

@app.route('/api/grijac/stanje', methods=['GET'])
def get_grijac_stanje():
    """Vraća stanje grijača"""
    return jsonify(current_state['aktuatori']['grijac'])

@app.route('/api/test_connection', methods=['GET'])
def test_connection():
    """Testira konekciju sa glavnom aplikacijom"""
    try:
        response = requests.get(f'{MAIN_APP_URL}/api/senzori/beton', timeout=5)
        return jsonify({
            'success': True,
            'main_app_status': response.status_code,
            'message': 'Konekcija sa glavnom aplikacijom uspešna'
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Ne mogu da se povezem sa glavnom aplikacijom na portu 5000'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def auto_simulate():
    """Automatska simulacija podataka (opciono)"""
    while True:
        try:
            # Simuliraj manje varijacije u podacima
            import random
            
            # Temperatura betona
            current_state['senzori']['beton']['temperatura'] += random.uniform(-0.5, 0.5)
            current_state['senzori']['beton']['vlaznost'] += random.uniform(-1, 1)
            
            # Temperatura površine
            current_state['senzori']['povrsina']['temperatura'] += random.uniform(-0.3, 0.3)
            current_state['senzori']['povrsina']['vlaznost'] += random.uniform(-0.8, 0.8)
            
            # Ograniči vrednosti
            for senzor in current_state['senzori'].values():
                senzor['temperatura'] = max(0, min(50, senzor['temperatura']))
                senzor['vlaznost'] = max(0, min(100, senzor['vlaznost']))
            
            time.sleep(30)  # Ažuriraj svakih 30 sekundi
            
        except Exception as e:
            print(f"Greška u auto simulaciji: {e}")
            time.sleep(60)

if __name__ == '__main__':
    print("🔧 IoT Kontroler Simulator pokrenut!")
    print("📡 Emuliram kontroler na http://localhost:3000")
    print("🎯 Glavna aplikacija treba da bude na http://localhost:5000")
    print("")
    print("Funkcionalnosti:")
    print("- Postavljanje stanja senzora i aktuatora")
    print("- Slanje pojedinačnih grešaka")
    print("- Slanje batch grešaka za testiranje")
    print("- API endpoints koje glavna aplikacija poziva")
    
    # Pokretanje auto simulacije u background thread-u
    # auto_thread = threading.Thread(target=auto_simulate, daemon=True)
    # auto_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=3000)