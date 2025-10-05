from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import random
import threading
import time

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_type TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            battery REAL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actuator_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actuator_type TEXT NOT NULL,
            status TEXT NOT NULL,
            battery REAL,
            temperature REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL,
            acknowledged BOOLEAN DEFAULT FALSE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Simulated data
current_data = {
    'beton_sensor': {
        'temperature': 22.5,
        'humidity': 65.0,
        'battery': 85,
        'status': 'online'
    },
    'vazduh_sensor': {
        'temperature': 20.1,
        'humidity': 58.7,
        'battery': 92,
        'status': 'online'
    },
    'pumpa': {
        'active': False,
        'battery': 78,
        'status': 'online',
        'remaining_time': 0
    },
    'grijac': {
        'active': False,
        'battery': 65,
        'temperature': 25.0,
        'status': 'online'
    }
}

def simulate_data():
    """Simulate sensor data changes"""
    while True:
        time.sleep(30)  # Update every 30 seconds
        
        # Simulate temperature variations
        current_data['beton_sensor']['temperature'] += random.uniform(-0.5, 0.5)
        current_data['vazduh_sensor']['temperature'] += random.uniform(-0.3, 0.3)
        
        # Simulate humidity changes
        current_data['beton_sensor']['humidity'] += random.uniform(-1.0, 1.0)
        current_data['vazduh_sensor']['humidity'] += random.uniform(-0.5, 0.5)
        
        # Clamp values to realistic ranges
        current_data['beton_sensor']['temperature'] = max(5, min(35, current_data['beton_sensor']['temperature']))
        current_data['vazduh_sensor']['temperature'] = max(0, min(40, current_data['vazduh_sensor']['temperature']))
        current_data['beton_sensor']['humidity'] = max(20, min(100, current_data['beton_sensor']['humidity']))
        current_data['vazduh_sensor']['humidity'] = max(20, min(100, current_data['vazduh_sensor']['humidity']))
        
        # Save to database
        save_sensor_data()
        
        # Check for alarms
        check_alarms()

def save_sensor_data():
    """Save current sensor data to database"""
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sensor_readings (sensor_type, temperature, humidity, battery, status)
        VALUES (?, ?, ?, ?, ?)
    ''', ('beton', current_data['beton_sensor']['temperature'], 
          current_data['beton_sensor']['humidity'], 
          current_data['beton_sensor']['battery'], 
          current_data['beton_sensor']['status']))
    
    cursor.execute('''
        INSERT INTO sensor_readings (sensor_type, temperature, humidity, battery, status)
        VALUES (?, ?, ?, ?, ?)
    ''', ('vazduh', current_data['vazduh_sensor']['temperature'], 
          current_data['vazduh_sensor']['humidity'], 
          current_data['vazduh_sensor']['battery'], 
          current_data['vazduh_sensor']['status']))
    
    conn.commit()
    conn.close()

def check_alarms():
    """Check for alarm conditions and create notifications"""
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    # Check temperature alarms
    beton_temp = current_data['beton_sensor']['temperature']
    if beton_temp < 0 or beton_temp > 40:
        cursor.execute('''
            INSERT INTO notifications (type, message, severity)
            VALUES (?, ?, ?)
        ''', ('temperature', f'Kritična temperatura betona: {beton_temp:.1f}°C', 'critical'))
    
    # Check humidity alarms
    beton_humidity = current_data['beton_sensor']['humidity']
    if beton_humidity < 40:
        cursor.execute('''
            INSERT INTO notifications (type, message, severity)
            VALUES (?, ?, ?)
        ''', ('humidity', f'Niska vlažnost betona: {beton_humidity:.1f}%', 'warning'))
    
    # Check battery levels
    for device, data in current_data.items():
        if 'battery' in data and data['battery'] < 20:
            cursor.execute('''
                INSERT INTO notifications (type, message, severity)
                VALUES (?, ?, ?)
            ''', ('battery', f'Niska baterija {device}: {data["battery"]}%', 'info'))
    
    conn.commit()
    conn.close()

def generate_random_notifications():
    """Generate random notifications for testing purposes"""
    notifications_templates = [
        {'type': 'system', 'message': 'Sistem uspješno sinhronizovan sa senzorom betona', 'severity': 'info'},
        {'type': 'battery', 'message': 'Nizak nivo baterije na senzoru vazduha ({}%)', 'severity': 'warning'},
        {'type': 'connection', 'message': 'Privremeni prekid konekcije sa pumpom', 'severity': 'warning'},
        {'type': 'temperature', 'message': 'Temperatura betona izvan preporučenog opsega: {}°C', 'severity': 'critical'},
        {'type': 'maintenance', 'message': 'Potrebno je održavanje grijača vode', 'severity': 'warning'},
        {'type': 'calibration', 'message': 'Sensor vazduha uspješno kalibrisan', 'severity': 'info'},
        {'type': 'safety', 'message': 'Kritična temperatura grijača: {}°C - automatski zaustavljen', 'severity': 'critical'},
        {'type': 'system', 'message': 'Pumpa za vodu završila sa radom ({}s)', 'severity': 'info'},
        {'type': 'humidity', 'message': 'Vlažnost betona ispod kritičnog nivoa: {}%', 'severity': 'critical'},
        {'type': 'network', 'message': 'Mreža obnovljena - svi uređaji povezani', 'severity': 'info'},
        {'type': 'power', 'message': 'Napajanje grijača nestabilno', 'severity': 'warning'},
        {'type': 'data', 'message': 'Anomalija u podacima senzora betona - provjeriti kalibracju', 'severity': 'warning'},
        {'type': 'success', 'message': 'Automatska kalibracija senzora završena uspješno', 'severity': 'info'},
        {'type': 'alert', 'message': 'Prekoračen maksimalni broj pokušaja konekcije', 'severity': 'critical'},
        {'type': 'maintenance', 'message': 'Redovno održavanje sistema zakazano za sutra', 'severity': 'info'},
    ]
    
    while True:
        time.sleep(random.randint(10, 30))  # Random interval between 10-30 seconds
        
        # 80% chance to generate a notification
        if random.random() < 0.8:
            template = random.choice(notifications_templates)
            message = template['message']
            
            # Fill in random values for placeholders
            if '{}' in message:
                if 'baterije' in message:
                    message = message.format(random.randint(5, 25))
                elif 'temperatura' in message.lower():
                    message = message.format(random.randint(-5, 50))
                elif 'vlažnost' in message.lower():
                    message = message.format(random.randint(15, 35))
                elif 'radom' in message:
                    message = message.format(random.randint(60, 300))
                else:
                    message = message.format(random.randint(1, 100))
            
            conn = sqlite3.connect('iot_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications (type, message, severity)
                VALUES (?, ?, ?)
            ''', (template['type'], message, template['severity']))
            
            conn.commit()
            conn.close()
            
            print(f"🔔 Generated random notification: {message} ({template['severity']})")

# API Routes
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get current dashboard data"""
    return jsonify(current_data)

@app.route('/api/senzori/beton', methods=['GET'])
def get_beton_sensor():
    """Get concrete sensor data"""
    data = current_data['beton_sensor']
    return jsonify({
        'temperatura': data['temperature'],
        'vlaznost': data['humidity'],
        'baterija': data['battery'],
        'greska': None if data['status'] == 'online' else 'offline'
    })

@app.route('/api/senzori/povrsina', methods=['GET'])
def get_povrsina_sensor():
    """Get surface/air sensor data"""
    data = current_data['vazduh_sensor']
    return jsonify({
        'temperatura': data['temperature'],
        'vlaznost': data['humidity'],
        'baterija': data['battery'],
        'greska': None if data['status'] == 'online' else 'offline'
    })

@app.route('/api/senzori/vazduh', methods=['GET'])
def get_vazduh_sensor():
    """Get air sensor data (alias for compatibility)"""
    return get_povrsina_sensor()

@app.route('/api/pumpa/stanje', methods=['GET'])
def get_pumpa_status():
    """Get pump status"""
    data = current_data['pumpa']
    return jsonify({
        'aktivna': data['active'],
        'baterija': data['battery'],
        'greska': None if data['status'] == 'online' else 'offline'
    })

@app.route('/api/grijac/stanje', methods=['GET'])
def get_grijac_status():
    """Get heater status"""
    data = current_data['grijac']
    return jsonify({
        'aktivan': data['active'],
        'temperatura': data['temperature'],
        'baterija': data['battery'],
        'greska': None if data['status'] == 'online' else 'offline'
    })

@app.route('/api/greska', methods=['POST'])
def report_error():
    """Receive error reports from controller"""
    data = request.json
    if not isinstance(data, list):
        data = [data]  # Convert single error to list
    
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    for error in data:
        uredjaj = error.get('uredjaj', 'nepoznat')
        tip = error.get('tip', 'greska')
        vreme = error.get('vreme', datetime.now().isoformat())
        
        # Map error type to severity
        severity_map = {
            'niska_baterija': 'warning',
            'niska_vlaznost': 'critical',
            'visoka_temperatura': 'critical', 
            'niska_temperatura': 'critical',
            'greska_senzora': 'warning',
            'prekid_komunikacije': 'warning',
            'kritična_temperatura_grijaca': 'critical',
            'system_maintenance': 'info'
        }
        
        severity = severity_map.get(tip, 'warning')
        
        # Create appropriate message
        message_templates = {
            'niska_baterija': f'Niska baterija na {uredjaj}',
            'niska_vlaznost': f'Kritično niska vlažnost na {uredjaj}',
            'visoka_temperatura': f'Kritično visoka temperatura na {uredjaj}',
            'niska_temperatura': f'Kritično niska temperatura na {uredjaj}',
            'greska_senzora': f'Greška senzora: {uredjaj}',
            'prekid_komunikacije': f'Prekid komunikacije sa {uredjaj}',
            'kritična_temperatura_grijaca': f'Kritična temperatura grijača: {uredjaj}',
            'system_maintenance': f'Potrebno održavanje: {uredjaj}'
        }
        
        message = message_templates.get(tip, f'Greška na {uredjaj}: {tip}')
        
        cursor.execute('''
            INSERT INTO notifications (type, message, severity, acknowledged, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (tip, message, severity, False, vreme))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'received': len(data)})
@app.route('/api/istorija', methods=['GET'])

@app.route('/api/grijac/upravljanje', methods=['POST'])
def control_grijac():
    """Control heater"""
    data = request.json
    action = data.get('akcija')
    
    if action == 'pokreni':
        target_temp = data.get('ciljna_temperatura', 50)
        current_data['grijac']['active'] = True
        current_data['grijac']['target_temperature'] = target_temp
        return jsonify({'uspjeh': True, 'poruka': f'Grijač pokrenut, ciljna temperatura {target_temp}°C'})
    
    elif action == 'zaustavi':
        current_data['grijac']['active'] = False
        return jsonify({'uspjeh': True, 'poruka': 'Grijač zaustavljen'})
    
    return jsonify({'uspjeh': False, 'poruka': 'Nepoznata akcija'})

@app.route('/api/istorija', methods=['GET'])
def get_history():
    """Get historical data"""
    hours = request.args.get('hours', 24, type=int)
    
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    # Get data from last N hours
    since = datetime.now() - timedelta(hours=hours)
    
    cursor.execute('''
        SELECT sensor_type, temperature, humidity, timestamp
        FROM sensor_readings
        WHERE timestamp > ?
        ORDER BY timestamp ASC
    ''', (since,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Group by sensor type
    history = {'beton': [], 'vazduh': []}
    
    for row in rows:
        sensor_type, temp, humidity, timestamp = row
        if sensor_type in history:
            history[sensor_type].append({
                'temperature': temp,
                'humidity': humidity,
                'timestamp': timestamp
            })
    
    return jsonify(history)

@app.route('/api/notifikacije', methods=['GET'])
def get_notifications():
    """Get all notifications"""
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, type, message, severity, acknowledged, timestamp
        FROM notifications
        ORDER BY timestamp DESC
        LIMIT 50
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    notifications = []
    for row in rows:
        notifications.append({
            'id': row[0],
            'type': row[1],
            'message': row[2],
            'severity': row[3],
            'acknowledged': row[4],
            'timestamp': row[5]
        })
    
    return jsonify(notifications)

@app.route('/api/notifikacije/<int:notification_id>/acknowledge', methods=['POST'])
def acknowledge_notification(notification_id):
    """Acknowledge a notification"""
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE notifications
        SET acknowledged = TRUE
        WHERE id = ?
    ''', (notification_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'uspjeh': True})

@app.route('/api/notifikacije/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification"""
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM notifications
        WHERE id = ?
    ''', (notification_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'uspjeh': True})

@app.route('/api/notifikacije/clear', methods=['POST'])
def clear_all_notifications():
    """Clear all acknowledged notifications"""
    conn = sqlite3.connect('iot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM notifications
        WHERE acknowledged = TRUE
    ''')
    
    conn.commit()
    conn.close()
    
    return jsonify({'uspjeh': True})

if __name__ == '__main__':
    init_db()
    
    # Start simulation thread
    simulation_thread = threading.Thread(target=simulate_data, daemon=True)
    simulation_thread.start()
    
    # Start random notifications thread
    notifications_thread = threading.Thread(target=generate_random_notifications, daemon=True)
    notifications_thread.start()
    
    print("🚀 IoT Backend pokrenut sa random notifikacijama!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
