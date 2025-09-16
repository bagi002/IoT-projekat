#!/usr/bin/env python3
"""
Test skript za generisanje JSON podataka grejaca
Ovaj skript simulira ponašanje Python skripte koja čita podatke sa senzora
i zapisuje ih u JSON format koji C++ program može da parsira.
"""

import json
import random
import time
import os

def generate_sensor_data():
    """Generiše random podatke senzora u JSON formatu"""
    
    # Random temperatura između 15 i 35 stepeni
    temperatura = round(random.uniform(15.0, 35.0), 1)
    
    
    # Random baterija između 10 i 100 procenata
    baterija = random.randint(10, 100)
    
    # 80% šanse da nema greške, 20% šanse da ima grešku
    if random.random() < 0.8:
        greska = None
    else:
        greske = [
            "Niska baterija",
            "Grejac neispravan",
            "Komunikacijska greška",
            "Previsoka temperatura"
        ]
        greska = random.choice(greske)
    
    return { 
        "baterija": baterija,
        "greska": greska
    }

def write_json_to_file(data, filename="podaci.json"):
    """Zapisuje JSON podatke u datoteku"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Greška pri pisanju u datoteku: {e}")
        return False

def test_with_specific_data():
    """Testira sa specifičnim podacima koje ste naveli"""
    test_data = [
        {"baterija": 85, "greska": None},
        {"baterija": 92, "greska": None},
        {"baterija": 67, "greska": "Niska baterija"},
        {"baterija": 15, "greska": "Grejac neispravan"}
    ]
    
    print("=== TEST SA SPECIFICNIM PODACIMA ===")
    for i, data in enumerate(test_data):
        print(f"\nTest {i+1}: {json.dumps(data, ensure_ascii=False)}")
        write_json_to_file(data)
        print("Podaci zapisani u podaci.json - proverite C++ program")
        input("Pritisnite Enter za sledeći test...")

def continuous_mode():
    """Kontinuirani mod - generiše nove podatke svakih 10 sekundi"""
    print("=== KONTINUIRANI MOD ===")
    print("Generiše nove podatke svakih 10 sekundi. Pritisnite Ctrl+C za izlaz.")
    
    try:
        while True:
            data = generate_sensor_data()
            if write_json_to_file(data):
                print(f"Novi podaci: {json.dumps(data, ensure_ascii=False)}")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nZaustavljeno od strane korisnika.")

def main():
    print("Python Test Skript za grejac")
    print("="*40)
    print("1. Test sa specifičnim podacima")
    print("2. Kontinuirani mod (generiše nove podatke svakih 10s)")
    print("3. Generiši jedan set podataka i izađi")
    
    choice = input("\nUnesite izbor (1-3): ").strip()
    
    if choice == "1":
        test_with_specific_data()
    elif choice == "2":
        continuous_mode()
    elif choice == "3":
        data = generate_sensor_data()
        write_json_to_file(data)
        print(f"Generirani podaci: {json.dumps(data, ensure_ascii=False)}")
        print("Podaci zapisani u podaci.json")
    else:
        print("Nevaljan izbor!")

if __name__ == "__main__":
    main()