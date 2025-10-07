"""
JSON Manager za upravljanje JSON fajlovima simulacije
Centralizovano čitanje i pisanje svih simulacionih podataka
"""

import json
import os
from typing import Dict, Any, Optional


class JSONManager:
    """
    Klasa za upravljanje JSON fajlovima simulacije
    Obezbeđuje centralizovano čitanje i pisanje podataka
    """
    
    def __init__(self, sim_data_path: str):
        """
        Inicijalizacija JSON managera
        
        Args:
            sim_data_path (str): Putanja do SimData foldera
        """
        self.sim_data_path = sim_data_path
        self.ensure_data_directory()
        
        # Definisanje putanja JSON fajlova
        self.files = {
            'time': os.path.join(sim_data_path, 'time.json'),
            'concrete': os.path.join(sim_data_path, 'BETON.JSON'),
            'air': os.path.join(sim_data_path, 'VAZDUH.JSON'),
            'batteries': os.path.join(sim_data_path, 'BATERIJE.JSON'),
            'actuators': os.path.join(sim_data_path, 'AKTUATORI.JSON')
        }
    
    def ensure_data_directory(self):
        """Kreiranje SimData direktorijuma ako ne postoji"""
        os.makedirs(self.sim_data_path, exist_ok=True)
    
    def load_json(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        Učitavanje JSON fajla
        
        Args:
            file_key (str): Ključ fajla iz self.files
            
        Returns:
            Optional[Dict[str, Any]]: Učitani podaci ili None ako fajl ne postoji
        """
        try:
            file_path = self.files.get(file_key)
            if not file_path or not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Greška pri učitavanju {file_key}: {e}")
            return None
    
    def save_json(self, file_key: str, data: Dict[str, Any]) -> bool:
        """
        Snimanje podataka u JSON fajl
        
        Args:
            file_key (str): Ključ fajla iz self.files
            data (Dict[str, Any]): Podaci za snimanje
            
        Returns:
            bool: True ako je snimanje uspešno, False inače
        """
        try:
            file_path = self.files.get(file_key)
            if not file_path:
                return False
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Greška pri snimanju {file_key}: {e}")
            return False
    
    # Specifične metode za različite tipove podataka
    
    def load_time(self) -> Optional[Dict[str, Any]]:
        """
        Učitavanje podataka o vremenu simulacije
        
        Returns:
            Optional[Dict[str, Any]]: Podaci o vremenu ili None
        """
        return self.load_json('time')
    
    def save_time(self, time_data: Dict[str, Any]) -> bool:
        """
        Snimanje podataka o vremenu simulacije
        
        Args:
            time_data (Dict[str, Any]): Podaci o vremenu
            
        Returns:
            bool: True ako je snimanje uspešno
        """
        return self.save_json('time', time_data)
    
    def load_concrete(self) -> Optional[Dict[str, Any]]:
        """
        Učitavanje podataka o betonu
        
        Returns:
            Optional[Dict[str, Any]]: Podaci o betonu ili None
        """
        return self.load_json('concrete')
    
    def save_concrete(self, concrete_data: Dict[str, Any]) -> bool:
        """
        Snimanje podataka o betonu
        
        Args:
            concrete_data (Dict[str, Any]): Podaci o betonu
            
        Returns:
            bool: True ako je snimanje uspešno
        """
        return self.save_json('concrete', concrete_data)
    
    def load_air(self) -> Optional[Dict[str, Any]]:
        """
        Učitavanje podataka o vazduhu
        
        Returns:
            Optional[Dict[str, Any]]: Podaci o vazduhu ili None
        """
        return self.load_json('air')
    
    def save_air(self, air_data: Dict[str, Any]) -> bool:
        """
        Snimanje podataka o vazduhu
        
        Args:
            air_data (Dict[str, Any]): Podaci o vazduhu
            
        Returns:
            bool: True ako je snimanje uspešno
        """
        return self.save_json('air', air_data)
    
    def load_batteries(self) -> Optional[Dict[str, Any]]:
        """
        Učitavanje podataka o baterijama
        
        Returns:
            Optional[Dict[str, Any]]: Podaci o baterijama ili None
        """
        return self.load_json('batteries')
    
    def save_batteries(self, battery_data: Dict[str, Any]) -> bool:
        """
        Snimanje podataka o baterijama
        
        Args:
            battery_data (Dict[str, Any]): Podaci o baterijama
            
        Returns:
            bool: True ako je snimanje uspešno
        """
        return self.save_json('batteries', battery_data)
    
    def load_actuators(self) -> Optional[Dict[str, Any]]:
        """
        Učitavanje komandi za aktuatore
        
        Returns:
            Optional[Dict[str, Any]]: Komande za aktuatore ili None
        """
        actuator_data = self.load_json('actuators')
        
        # Vraćanje default vrednosti ako fajl ne postoji
        if actuator_data is None:
            return {
                'pump': {
                    'status': 0,  # 0 = OFF, 1 = ON
                    'runtime_minutes': 0
                },
                'heater': {
                    'status': 0,  # 0 = OFF, 1 = ON
                    'temperature': 25.0
                }
            }
        
        return actuator_data
    
    def save_actuators(self, actuator_data: Dict[str, Any]) -> bool:
        """
        Snimanje komandi za aktuatore
        
        Args:
            actuator_data (Dict[str, Any]): Komande za aktuatore
            
        Returns:
            bool: True ako je snimanje uspešno
        """
        return self.save_json('actuators', actuator_data)
    
    def create_initial_files(self):
        """
        Kreiranje početnih JSON fajlova sa default vrednostima
        Poziva se pri prvom pokretanju simulacije
        """
        # Početno vreme
        if not os.path.exists(self.files['time']):
            initial_time = {
                'date': '2025-05-05',
                'time': '12:00:00',
                'step_minutes': 10
            }
            self.save_time(initial_time)
        
        # Početno stanje betona
        if not os.path.exists(self.files['concrete']):
            initial_concrete = {
                'temperature': 25.0,
                'humidity': 90.0,
                'battery_level': 100.0
            }
            self.save_concrete(initial_concrete)
        
        # Početno stanje vazduha
        if not os.path.exists(self.files['air']):
            initial_air = {
                'temperature': 25.0,
                'humidity': 60.0,
                'battery_level': 100.0
            }
            self.save_air(initial_air)
        
        # Početno stanje baterija
        if not os.path.exists(self.files['batteries']):
            initial_batteries = {
                'pump_battery': 100.0,
                'heater_battery': 100.0
            }
            self.save_batteries(initial_batteries)
        
        # Početno stanje aktuatora
        if not os.path.exists(self.files['actuators']):
            initial_actuators = {
                'pump': {
                    'status': 0,
                    'runtime_minutes': 0
                },
                'heater': {
                    'status': 0,
                    'temperature': 25.0
                }
            }
            self.save_actuators(initial_actuators)
    
    def get_file_paths(self) -> Dict[str, str]:
        """
        Dobijanje putanja svih JSON fajlova
        
        Returns:
            Dict[str, str]: Rečnik sa putanjama fajlova
        """
        return self.files.copy()
    
    def file_exists(self, file_key: str) -> bool:
        """
        Provera da li JSON fajl postoji
        
        Args:
            file_key (str): Ključ fajla iz self.files
            
        Returns:
            bool: True ako fajl postoji
        """
        file_path = self.files.get(file_key)
        return file_path is not None and os.path.exists(file_path)
    
    def clear_all_data(self):
        """
        Brisanje svih JSON fajlova
        Koristi se za reset simulacije
        """
        for file_path in self.files.values():
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Greška pri brisanju {file_path}: {e}")