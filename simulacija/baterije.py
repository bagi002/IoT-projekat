#!/usr/bin/env python3
import json
import time
import random
import os

# Putanja do JSON fajla
JSON_FILE = "BATERIJE.json"

def read_battery_data():
    """Čita postojeće podatke o baterijama iz JSON fajla"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    # Vraća početne vrednosti ako fajl ne postoji ili je prazan
    return {
        "pump_battery": 100,
        "heater_battery": 100
    }

def write_battery_data(data):
    """Piše podatke o baterijama u JSON fajl"""
    try:
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Baterije ažurirane: Pumpa {data['pump_battery']}%, Grejač {data['heater_battery']}%")
    except Exception as e:
        print(f"Greška pri pisanju u fajl: {e}")

def simulate_battery_drain(current_level):
    """Simulira pražnjenje baterije - smanjuje za 1-3%"""
    drain = random.randint(1, 3)
    new_level = max(0, current_level - drain)
    return new_level

def simulate_battery_charge(current_level):
    """Simulira punjenje baterije kada je niska"""
    if current_level < 20:
        charge = random.randint(5, 15)
        return min(100, current_level + charge)
    return current_level

def main():
    print("Pokretanje simulacije baterija...")
    print(f"Podaci se čuvaju u: {JSON_FILE}")
    print("Pritisnite Ctrl+C za prekid")
    
    try:
        while True:
            # Učitaj trenutne podatke
            battery_data = read_battery_data()
            
            # Simuliraj promene u bateriji
            battery_data["pump_battery"] = simulate_battery_charge(
                simulate_battery_drain(battery_data["pump_battery"])
            )
            battery_data["heater_battery"] = simulate_battery_charge(
                simulate_battery_drain(battery_data["heater_battery"])
            )
            
            # Sačuvaj ažurirane podatke
            write_battery_data(battery_data)
            
            # Čekaj 10 sekundi
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nSimulacija prekinuta.")
    except Exception as e:
        print(f"Neočekivana greška: {e}")

if __name__ == "__main__":
    main()
