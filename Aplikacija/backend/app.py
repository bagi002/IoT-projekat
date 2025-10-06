from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import sqlite3
import requests
import threading
import time
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# URL kontrolera (test aplikacije)
KONTROLER_URL = 'http://localhost:3000'

# Stanja uređaja - početno sve neaktivno
device_status = {
    'beton_senzor': {'active': False, 'last_update': None, 'data': None},
    'povrsina_senzor': {'active': False, 'last_update': None, 'data': None},
    'pumpa': {'active': False, 'last_update': None, 'data': None},
    'grijac': {'active': False, 'last_update': None, 'data': None}
}

# Tracker za poslednje snimanje podataka (za 10-minutni interval)
last_sensor_save = {
    'beton_senzor': None,
    'povrsina_senzor': None
}

# Simulovano vreme funkcije
def get_sim_time_path():
    """Vraća apsolutni put do time.json fajla"""
    # Idemo iz backend direktorijuma do root-a projekta (Aplikacija/backend -> IoT projekat)
    backend_dir = os.path.dirname(os.path.abspath(__file__))  # /home/bagi/Desktop/IoT projekat/Aplikacija/backend
    aplikacija_dir = os.path.dirname(backend_dir)  # /home/bagi/Desktop/IoT projekat/Aplikacija
    project_root = os.path.dirname(aplikacija_dir)  # /home/bagi/Desktop/IoT projekat
    time_path = os.path.join(project_root, 'SimData', 'time.json')
    print(f"🔍 [DEBUG] Looking for time.json at: {time_path}")
    print(f"🔍 [DEBUG] File exists: {os.path.exists(time_path)}")
    return time_path

def read_sim_time():
    """Čita simulovano vreme iz SimData/time.json"""
    try:
        time_path = get_sim_time_path()
        
        # Proverava da li fajl postoji
        if not os.path.exists(time_path):
            print(f"❌ [ERROR] Time file does not exist: {time_path}")
            return datetime.now()
        
        print(f"📖 [DEBUG] Reading time from: {time_path}")
        with open(time_path, 'r', encoding='utf-8') as f:
            time_data = json.load(f)
        
        print(f"📅 [DEBUG] Loaded time data: {time_data}")
        
        # Kombina datum i vreme u datetime objekat
        date_str = time_data['date']
        time_str = time_data['time']
        datetime_str = f"{date_str} {time_str}"
        print(f"🕐 [DEBUG] Parsing datetime: {datetime_str}")
        sim_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        
        print(f"✅ [SUCCESS] Sim time parsed: {sim_datetime}")
        return sim_datetime
    except Exception as e:
        print(f"⚠️ [WARNING] Could not read sim time: {e}, using system time")
        return datetime.now()

def get_current_sim_time():
    """Vraća trenutno simulovano vreme"""
    return read_sim_time()

def format_sim_time_iso(sim_time=None):
    """Formatira simulovano vreme u ISO format"""
    if sim_time is None:
        sim_time = get_current_sim_time()
    return sim_time.isoformat() + 'Z'

def should_save_sensor_data(device_type):
    """Proverava da li je vreme za novo snimanje podataka (svakih 10 minuta simulovano vreme)"""
    current_sim_time = get_current_sim_time()
    last_save = last_sensor_save.get(device_type)
    
    if last_save is None:
        print(f"📝 [SAVE_CHECK] First save for {device_type}")
        return True
    
    time_diff = current_sim_time - last_save
    minutes_diff = time_diff.total_seconds() / 60
    
    print(f"📝 [SAVE_CHECK] {device_type}: {minutes_diff:.1f} minutes since last save")
    
    # Čuva svakih 10 minuta ili više
    return minutes_diff >= 10

def init_db():
    """Inicijalizuje SQLite bazu podataka"""
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    # Tabela za notifikacije/greške
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uredjaj TEXT NOT NULL,
            tip TEXT NOT NULL,
            vreme TEXT NOT NULL,
            poruka TEXT NOT NULL,
            procitana BOOLEAN DEFAULT FALSE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela za istoriju podataka senzora
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_type TEXT NOT NULL,
            temperatura REAL,
            vlaznost REAL,
            baterija INTEGER,
            timestamp TEXT NOT NULL,
            sim_time TEXT NOT NULL
        )
    ''')
    
    # Migracija - dodaj sim_time kolonu ako ne postoji
    try:
        cursor.execute('ALTER TABLE sensor_history ADD COLUMN sim_time TEXT')
        print("📊 Added sim_time column to sensor_history table")
    except sqlite3.OperationalError:
        print("📊 sim_time column already exists in sensor_history table")
    
    # Ažuriraj postojeće zapise bez sim_time
    cursor.execute('UPDATE sensor_history SET sim_time = timestamp WHERE sim_time IS NULL OR sim_time = ""')
    updated_rows = cursor.rowcount
    if updated_rows > 0:
        print(f"📊 Updated {updated_rows} records with sim_time")
    
    conn.commit()
    conn.close()
    print("📊 Baza podataka inicijalizovana")

def fetch_device_data():
    """Dohvata podatke sa kontrolera svakih 10 sekundi"""
    while True:
        try:
            # Dohvati podatke sa kontrolera
            endpoints = [
                ('beton_senzor', '/api/senzori/beton'),
                ('povrsina_senzor', '/api/senzori/povrsina'),
                ('pumpa', '/api/pumpa/stanje'),
                ('grijac', '/api/grijac/stanje')
            ]
            
            for device_name, endpoint in endpoints:
                try:
                    response = requests.get(f"{KONTROLER_URL}{endpoint}", timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        device_status[device_name] = {
                            'active': True,
                            'last_update': get_current_sim_time(),
                            'data': data
                        }
                        
                        # Sačuvaj podatke senzora u istoriju svakih 10 minuta (simulovano vreme)
                        if device_name in ['beton_senzor', 'povrsina_senzor']:
                            if should_save_sensor_data(device_name):
                                save_sensor_data(device_name, data)
                                last_sensor_save[device_name] = get_current_sim_time()
                        
                        print(f"✅ {device_name}: {data}")
                    else:
                        print(f"❌ {device_name}: HTTP {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"🔴 {device_name}: Konekcija neuspešna - {e}")
                    
            # Proveri koje uređaje treba označiti kao neaktivne (preko 1 min bez odgovora)
            check_device_timeouts()
            
        except Exception as e:
            print(f"Greška u fetch_device_data: {e}")
            
        time.sleep(10)  # Svakih 10 sekundi

def check_device_timeouts():
    """Označava uređaje kao neaktivne ako nisu odgovorili preko 1 minuta"""
    timeout_limit = timedelta(minutes=1)
    current_time = get_current_sim_time()
    
    for device_name, status in device_status.items():
        if status['last_update'] is not None:
            time_since_update = current_time - status['last_update']
            if time_since_update > timeout_limit and status['active']:
                device_status[device_name]['active'] = False
                print(f"⏰ {device_name}: Označen kao neaktivan (timeout)")

def save_sensor_data(device_type, data):
    """Čuva podatke senzora u bazu za istoriju sa simulovanim vremenom"""
    try:
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        sim_time = get_current_sim_time()
        sim_time_str = format_sim_time_iso(sim_time)
        
        print(f"💾 [SAVE] Saving {device_type} data at sim time: {sim_time_str}")
        
        cursor.execute('''
            INSERT INTO sensor_history (device_type, temperatura, vlaznost, baterija, timestamp, sim_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            device_type,
            data.get('temperatura'),
            data.get('vlaznost'),
            data.get('baterija'),
            sim_time.strftime('%Y-%m-%d %H:%M:%S'),
            sim_time_str
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Greška pri čuvanju podataka: {e}")

# API ENDPOINTS PREMA SPECIFIKACIJI

@app.route('/api/senzori/beton', methods=['GET'])
def get_beton_sensor():
    """Vraća podatke senzora betona"""
    if device_status['beton_senzor']['active'] and device_status['beton_senzor']['data']:
        return jsonify(device_status['beton_senzor']['data'])
    else:
        return jsonify({
            'temperatura': None,
            'vlaznost': None,
            'baterija': None,
            'greska': 'device_offline'
        }), 503

@app.route('/api/senzori/povrsina', methods=['GET'])
def get_povrsina_sensor():
    """Vraća podatke senzora površine"""
    if device_status['povrsina_senzor']['active'] and device_status['povrsina_senzor']['data']:
        return jsonify(device_status['povrsina_senzor']['data'])
    else:
        return jsonify({
            'temperatura': None,
            'vlaznost': None,
            'baterija': None,
            'greska': 'device_offline'
        }), 503

@app.route('/api/pumpa/stanje', methods=['GET'])
def get_pumpa_status():
    """Vraća stanje pumpe"""
    if device_status['pumpa']['active'] and device_status['pumpa']['data']:
        return jsonify(device_status['pumpa']['data'])
    else:
        return jsonify({
            'aktivna': False,
            'baterija': None,
            'greska': 'device_offline'
        }), 503

@app.route('/api/grijac/stanje', methods=['GET'])
def get_grijac_status():
    """Vraća stanje grijača"""
    if device_status['grijac']['active'] and device_status['grijac']['data']:
        return jsonify(device_status['grijac']['data'])
    else:
        return jsonify({
            'aktivan': False,
            'temperatura': None,
            'baterija': None,
            'greska': 'device_offline'
        }), 503

@app.route('/api/greska', methods=['POST'])
def report_error():
    """Prima greške i čuva ih kao notifikacije"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Nema podataka'}), 400
        
        uredjaj = data.get('uredjaj')
        tip = data.get('tip')
        vreme = data.get('vreme', format_sim_time_iso())
        poruka = data.get('poruka', f'{tip} na uređaju {uredjaj}')
        
        if not uredjaj or not tip:
            return jsonify({'error': 'Nedostaju polja: uredjaj, tip'}), 400
        
        # Sačuvaj u bazu kao notifikaciju
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (uredjaj, tip, vreme, poruka, procitana)
            VALUES (?, ?, ?, ?, ?)
        ''', (uredjaj, tip, vreme, poruka, False))
        
        conn.commit()
        conn.close()
        
        print(f"🚨 Nova greška: {poruka} ({tip}) - {uredjaj}")
        
        # Vrati odgovor prema specifikaciji
        return jsonify([{
            'uredjaj': uredjaj,
            'tip': tip,
            'vreme': vreme
        }])
        
    except Exception as e:
        print(f"Greška u POST /api/greska: {e}")
        return jsonify({'error': str(e)}), 500

# DASHBOARD I FRONTEND ENDPOINTS

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Vraća podatke za dashboard"""
    dashboard_data = {}
    
    for device_name, status in device_status.items():
        dashboard_data[device_name] = {
            'active': status['active'],
            'last_update': status['last_update'].isoformat() if status['last_update'] else None,
            'data': status['data'] if status['active'] else None
        }
    
    print(f"🖥️  Dashboard request - returning: {dashboard_data}")
    return jsonify(dashboard_data)

@app.route('/api/notifikacije', methods=['GET'])
def get_notifications():
    """Dohvata sve notifikacije"""
    try:
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, uredjaj, tip, vreme, poruka, procitana, timestamp
            FROM notifications
            ORDER BY timestamp DESC
            LIMIT 100
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notifications.append({
                'id': row[0],
                'uredjaj': row[1],
                'tip': row[2],
                'vreme': row[3],
                'poruka': row[4],
                'procitana': bool(row[5]),
                'timestamp': row[6]
            })
        
        return jsonify({
            'success': True,
            'notifikacije': notifications
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifikacije/procitaj', methods=['POST'])
def mark_notification_read():
    """Označava notifikaciju kao pročitanu/nepročitanu"""
    try:
        data = request.json
        notification_id = data.get('id')
        procitana = data.get('procitana', True)
        
        if not notification_id:
            return jsonify({'success': False, 'error': 'Nedostaje ID notifikacije'}), 400
        
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications
            SET procitana = ?
            WHERE id = ?
        ''', (procitana, notification_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Notifikacija nije pronađena'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Notifikacija označena kao {"pročitana" if procitana else "nepročitana"}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifikacije/procitaj-sve', methods=['POST'])
def mark_all_notifications_read():
    """Označava sve notifikacije kao pročitane"""
    try:
        print(f"📝 [DEBUG] Mark all notifications as read request received")
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications
            SET procitana = TRUE
            WHERE procitana = FALSE
        ''')
        
        updated_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ [DEBUG] Marked {updated_count} notifications as read")
        return jsonify({
            'success': True, 
            'message': f'Označeno {updated_count} notifikacija kao pročitano',
            'updated_count': updated_count
        })
        
    except Exception as e:
        print(f"❌ [DEBUG] Error marking all notifications as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifikacije/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Briše određenu notifikaciju"""
    try:
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM notifications
            WHERE id = ?
        ''', (notification_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Notifikacija nije pronađena'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Notifikacija obrisana'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifikacije/obrisi-procitane', methods=['DELETE'])
def clear_read_notifications():
    """Briše samo pročitane notifikacije"""
    try:
        print(f"🗑️ [DEBUG] Clear read notifications request received")
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM notifications
            WHERE procitana = TRUE
        ''')
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ [DEBUG] Deleted {deleted_count} read notifications")
        return jsonify({
            'success': True, 
            'message': f'Obrisano {deleted_count} pročitanih notifikacija',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        print(f"❌ [DEBUG] Error deleting read notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifikacije/obrisi-sve', methods=['DELETE'])
def clear_all_notifications():
    """Briše sve notifikacije"""
    try:
        print(f"🗑️ [DEBUG] Clear all notifications request received")
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM notifications')
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ [DEBUG] Deleted {deleted_count} notifications")
        return jsonify({
            'success': True, 
            'message': f'Obrisano {deleted_count} notifikacija',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        print(f"❌ [DEBUG] Error deleting all notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sim-time', methods=['GET'])
def get_sim_time():
    """Vraća trenutno simulovano vreme"""
    try:
        sim_time = get_current_sim_time()
        return jsonify({
            'success': True,
            'iso_time': format_sim_time_iso(sim_time),
            'sim_time': format_sim_time_iso(sim_time),  # Za kompatibilnost
            'formatted_time': sim_time.strftime('%Y-%m-%d %H:%M:%S'),
            'date': sim_time.strftime('%Y-%m-%d'),
            'time': sim_time.strftime('%H:%M:%S')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/istorija', methods=['GET'])
def get_history():
    """Vraća istoriju podataka senzora"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT device_type, temperatura, vlaznost, baterija, timestamp
            FROM sensor_history
            WHERE timestamp > datetime('now', '-{} hours')
            ORDER BY timestamp ASC
        '''.format(hours))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'device_type': row[0],
                'temperatura': row[1],
                'vlaznost': row[2],
                'baterija': row[3],
                'timestamp': row[4]
            })
    
        return jsonify(history)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# FRONTEND STRANICA
@app.route('/')
def frontend():
    """Jednostavna frontend stranica za praćenje statusa"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>IoT Sistem - Status</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
            .container { max-width: 1200px; margin: 0 auto; }
            .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
            .device-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .device-card.active { border-left: 4px solid #28a745; }
            .device-card.inactive { border-left: 4px solid #dc3545; }
            .status { font-weight: bold; }
            .active .status { color: #28a745; }
            .inactive .status { color: #dc3545; }
            .data { margin: 10px 0; }
            .header { text-align: center; color: #333; }
            .refresh-btn { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .last-update { font-size: 0.9em; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏗️ IoT Sistem za Nadzor Betona</h1>
                <p>Praćenje stanja uređaja u realnom vremenu</p>
                <button class="refresh-btn" onclick="location.reload()">🔄 Osveži</button>
            </div>
            
            <div class="status-grid" id="devices"></div>
            
            <div style="margin-top: 30px; text-align: center;">
                <p><strong>Napomene:</strong></p>
                <p>🟢 Zeleno = Uređaj aktivan (podaci pristigli u poslednji minut)</p>
                <p>🔴 Crveno = Uređaj neaktivan (nema podataka preko 1 minuta)</p>
                <p>📡 Sistem pokušava da dohvati podatke svakih 10 sekundi sa http://localhost:3000</p>
            </div>
        </div>
        
        <script>
            async function loadDeviceStatus() {
                try {
                    const response = await fetch('/api/dashboard');
                    const data = await response.json();
                    
                    const container = document.getElementById('devices');
                    container.innerHTML = '';
                    
                    const deviceNames = {
                        'beton_senzor': '🏗️ Senzor Betona',
                        'povrsina_senzor': '🌡️ Senzor Površine', 
                        'pumpa': '💧 Pumpa za Vodu',
                        'grijac': '🔥 Grijač Vode'
                    };
                    
                    for (const [deviceId, deviceData] of Object.entries(data)) {
                        const card = document.createElement('div');
                        card.className = `device-card ${deviceData.active ? 'active' : 'inactive'}`;
                        
                        let dataHtml = '';
                        if (deviceData.active && deviceData.data) {
                            const d = deviceData.data;
                            if (d.temperatura !== undefined) dataHtml += `<div>🌡️ Temperatura: ${d.temperatura}°C</div>`;
                            if (d.vlaznost !== undefined) dataHtml += `<div>💧 Vlažnost: ${d.vlaznost}%</div>`;
                            if (d.baterija !== undefined) dataHtml += `<div>🔋 Baterija: ${d.baterija}%</div>`;
                            if (d.aktivna !== undefined) dataHtml += `<div>⚡ Status: ${d.aktivna ? 'Aktivna' : 'Neaktivna'}</div>`;
                            if (d.aktivan !== undefined) dataHtml += `<div>⚡ Status: ${d.aktivan ? 'Aktivan' : 'Neaktivan'}</div>`;
                        } else {
                            dataHtml = '<div style="color: #dc3545;">❌ Nema podataka</div>';
                        }
                        
                        const lastUpdate = deviceData.last_update ? 
                            new Date(deviceData.last_update).toLocaleString() : 'Nikad';
                        
                        card.innerHTML = `
                            <h3>${deviceNames[deviceId] || deviceId}</h3>
                            <div class="status">${deviceData.active ? '🟢 AKTIVAN' : '🔴 NEAKTIVAN'}</div>
                            <div class="data">${dataHtml}</div>
                            <div class="last-update">Poslednji put: ${lastUpdate}</div>
                        `;
                        
                        container.appendChild(card);
                    }
                } catch (error) {
                    console.error('Greška pri učitavanju statusa:', error);
                }
            }
            
            // Učitaj status pri učitavanju stranice
            loadDeviceStatus();
            
            // Osveži svakih 5 sekundi
            setInterval(loadDeviceStatus, 5000);
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/api/sensor-history', methods=['GET'])
def get_sensor_history():
    """Vraća istoriju podataka senzora"""
    try:
        device_type = request.args.get('device_type')  # 'beton_senzor', 'povrsina_senzor' ili None za sve
        hours = request.args.get('hours', '24')  # Koliko sati unazad (default 24)
        limit = request.args.get('limit', '100')  # Maksimalan broj zapisa
        
        conn = sqlite3.connect('iot_data.db')
        cursor = conn.cursor()
        
        # Bazni upit
        query = '''
            SELECT id, device_type, temperatura, vlaznost, baterija, timestamp, sim_time
            FROM sensor_history
        '''
        params = []
        
        # Filter po device_type
        if device_type:
            query += ' WHERE device_type = ?'
            params.append(device_type)
        
        # Sortiraj po vremenu (najnoviji prvi)
        query += ' ORDER BY id DESC'
        
        # Limit
        query += ' LIMIT ?'
        params.append(int(limit))
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'device_type': row[1],
                'temperatura': row[2],
                'vlaznost': row[3],
                'baterija': row[4],
                'timestamp': row[5],
                'sim_time': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
        
    except Exception as e:
        print(f"❌ Error getting sensor history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    
    # Pokreni thread za dohvatanje podataka
    data_thread = threading.Thread(target=fetch_device_data, daemon=True)
    data_thread.start()
    
    print("")
    print("🚀 IoT Backend Application pokrenut!")
    print("📡 Listening na: http://localhost:5000")
    print("🎯 Očekuje kontroler na: http://localhost:3000")
    print("")
    print("📋 API Endpoints prema specifikaciji:")
    print("   GET  /api/senzori/beton")
    print("   GET  /api/senzori/povrsina") 
    print("   GET  /api/pumpa/stanje")
    print("   GET  /api/grijac/stanje")
    print("   POST /api/greska")
    print("")
    print("🖥️  Dashboard dostupan na: http://localhost:5000")
    print("🔄 Automatski dohvata podatke svakih 10 sekundi")
    print("⏰ Timeout za uređaje: 1 minut")
    print("")
    
    app.run(debug=True, host='0.0.0.0', port=5000)