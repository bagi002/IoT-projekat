#!/usr/bin/env python3
"""
Test skript za generisanje JSON podataka senzora vazduha
Ovaj skript simulira ponašanje Python skripte koja čita podatke sa senzora vazduha
i zapisuje ih u JSON format koji C++ program može da parsira.
"""

import json
import random
import time
import os

def generate_sensor_data():
    """Generiše random podatke senzora vazduha u JSON formatu"""
    
    # Random temperatura vazduha između -10 i 45 stepeni (širi opseg za spoljašnji vazduh)
    temperatura = round(random.uniform(-10.0, 45.0), 1)
    
    # Random vlažnost vazduha između 20 i 95 procenata
    vlaznost = round(random.uniform(20.0, 95.0), 1)

    # Random baterija između 10 i 100 procenata
    baterija = random.randint(10, 100)
    
    # 85% šanse da nema greške, 15% šanse da ima grešku
    if random.random() < 0.85:
        greska = None
    else:
        greske = [
            "Niska baterija",
            "Senzor vlažnosti neispravan",
            "Senzor temperature neispravan",
            "Komunikacijska greška",
            "Previsoka temperatura"
        ]
        greska = random.choice(greske)
    
    return {
        "temperatura": temperatura,
        "vlaznost": vlaznost, 
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
        {"temperatura": 25.5, "vlaznost": 65.2, "baterija": 85, "greska": None},
        {"temperatura": 22.1, "vlaznost": 58.7, "baterija": 92, "greska": None},
        {"temperatura": 28.3, "vlaznost": 45.1, "baterija": 67, "greska": "Niska baterija"},
        {"temperatura": 19.8, "vlaznost": 78.9, "baterija": 15, "greska": "Senzor vlažnosti neispravan"}
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
    print("Python Test Skript za Senzor Vazduha")
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