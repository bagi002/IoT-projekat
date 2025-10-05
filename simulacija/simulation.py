"""
Glavna simulaciona aplikacija za betonsku deku
Modularno dizajnirana za lako proširivanje i prilagođavanje
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta
import math
import threading
import time

from models.concrete_model import ConcreteModel
from models.air_model import AirModel
from models.battery_model import BatteryManager
from models.actuator_model import ActuatorModel
from utils.json_manager import JSONManager
from utils.simulation_time import SimulationTime


class SimulationApp:
    """
    Glavna klasa simulacione aplikacije
    Upravlja celokupnom simulacijom i GUI-jem
    """
    
    def __init__(self):
        """Inicijalizacija simulacione aplikacije"""
        self.root = tk.Tk()
        self.setup_window()
        
        # Kreiranje SimData foldera ako ne postoji
        self.sim_data_path = "/home/radov1c/Desktop/FTN/Letnji/IoT/IoT-projekat/simulacija/SimData"
        os.makedirs(self.sim_data_path, exist_ok=True)
        
        # Inicijalizacija komponenti
        self.json_manager = JSONManager(self.sim_data_path)
        self.sim_time = SimulationTime()
        self.battery_manager = BatteryManager()
        self.concrete_model = ConcreteModel()
        self.air_model = AirModel()
        self.actuator_model = ActuatorModel()
        
        # Simulacione varijable
        self.is_running = False
        self.step_minutes = 10  # Default korak simulacije u minutima
        self.external_temp = 25.0  # Početna spoljna temperatura
        self.external_humidity = 60.0  # Početna spoljna vlažnost
        
        # GUI komponente
        self.setup_gui()
        
        # Učitavanje početnog stanja
        self.load_initial_state()
    
    def setup_window(self):
        """Postavke glavnog prozora"""
        self.root.title("Simulacija Betonske Deke - IoT Projekat")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
    
    def setup_gui(self):
        """Kreiranje grafičkog interfejsa"""
        # Glavni container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguracija grid-a za resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Levi panel - kontrole
        self.setup_control_panel(main_frame)
        
        # Desni panel - status i podaci
        self.setup_status_panel(main_frame)
    
    def setup_control_panel(self, parent):
        """Kreiranje kontrolnog panela"""
        control_frame = ttk.LabelFrame(parent, text="Kontrole Simulacije", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Vreme simulacije
        time_frame = ttk.LabelFrame(control_frame, text="Vreme Simulacije", padding="5")
        time_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Trenutno vreme
        ttk.Label(time_frame, text="Trenutno vreme:").grid(row=0, column=0, sticky=tk.W)
        self.time_label = ttk.Label(time_frame, text="2025-05-05 12:00:00")
        self.time_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Korak simulacije
        ttk.Label(time_frame, text="Korak (minuti):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.step_var = tk.StringVar(value="10")
        step_entry = ttk.Entry(time_frame, textvariable=self.step_var, width=10)
        step_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # Dugmad za kontrolu
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.start_btn = ttk.Button(button_frame, text="Pokreni", command=self.start_simulation)
        self.start_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Zaustavi", command=self.stop_simulation, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.step_btn = ttk.Button(button_frame, text="Jedan Korak", command=self.single_step)
        self.step_btn.grid(row=0, column=2, padx=5)
        
        self.restart_btn = ttk.Button(button_frame, text="Restart", command=self.restart_simulation)
        self.restart_btn.grid(row=0, column=3, padx=5)
        
        # Spoljni uslovi
        self.setup_external_conditions(control_frame)
        
        # Baterije kontrole
        self.setup_battery_controls(control_frame)
    
    def setup_external_conditions(self, parent):
        """Kreiranje kontrola za spoljnje uslove"""
        ext_frame = ttk.LabelFrame(parent, text="Spoljnji Uslovi (Bazne vrednosti za podne)", padding="5")
        ext_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Temperatura
        ttk.Label(ext_frame, text="Bazna temp. u podne (°C):").grid(row=0, column=0, sticky=tk.W)
        self.ext_temp_var = tk.StringVar(value="25.0")
        temp_entry = ttk.Entry(ext_frame, textvariable=self.ext_temp_var, width=10)
        temp_entry.grid(row=0, column=1, padx=(10, 0))
        
        # Vlažnost
        ttk.Label(ext_frame, text="Bazna vlažnost u podne (%):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.ext_hum_var = tk.StringVar(value="60.0")
        hum_entry = ttk.Entry(ext_frame, textvariable=self.ext_hum_var, width=10)
        hum_entry.grid(row=1, column=1, padx=(10, 0), pady=(5, 0))
        
        # Objašnjenje
        info_label = ttk.Label(ext_frame, text="Napomena: Vrednosti variraju tokom dana", 
                              font=("TkDefaultFont", 8), foreground="gray")
        info_label.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Dugme za primenu
        apply_btn = ttk.Button(ext_frame, text="Primeni", command=self.apply_external_conditions)
        apply_btn.grid(row=3, column=0, columnspan=2, pady=(10, 0))
    
    def setup_battery_controls(self, parent):
        """Kreiranje kontrola za baterije"""
        bat_frame = ttk.LabelFrame(parent, text="Kontrola Baterija", padding="5")
        bat_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Lista baterija
        batteries = ["Senzor Beton", "Senzor Vazduh", "Pumpa", "Grijač"]
        
        for i, battery in enumerate(batteries):
            # Naziv baterije
            ttk.Label(bat_frame, text=f"{battery}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            
            # Checkbox za lošu bateriju
            bad_var = tk.BooleanVar()
            setattr(self, f"bad_battery_{i}", bad_var)
            bad_check = ttk.Checkbutton(bat_frame, text="Loša", variable=bad_var)
            bad_check.grid(row=i, column=1, padx=(10, 5), pady=2)
            
            # Dugme za ubijanje baterije
            kill_btn = ttk.Button(bat_frame, text="Ubij", 
                                command=lambda idx=i: self.kill_battery(idx))
            kill_btn.grid(row=i, column=2, padx=5, pady=2)
    
    def setup_status_panel(self, parent):
        """Kreiranje status panela"""
        status_frame = ttk.LabelFrame(parent, text="Status Simulacije", padding="10")
        status_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Notebook za tabove
        notebook = ttk.Notebook(status_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        # Tab za beton
        self.setup_concrete_tab(notebook)
        
        # Tab za vazduh
        self.setup_air_tab(notebook)
        
        # Tab za baterije
        self.setup_battery_tab(notebook)
        
        # Tab za aktuatore
        self.setup_actuator_tab(notebook)
    
    def setup_concrete_tab(self, parent):
        """Tab za prikaz stanja betona"""
        concrete_frame = ttk.Frame(parent, padding="10")
        parent.add(concrete_frame, text="Beton")
        
        # Labels za prikaz vrednosti
        ttk.Label(concrete_frame, text="Temperatura Betona:").grid(row=0, column=0, sticky=tk.W)
        self.concrete_temp_label = ttk.Label(concrete_frame, text="25.0°C")
        self.concrete_temp_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(concrete_frame, text="Vlažnost Betona:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.concrete_hum_label = ttk.Label(concrete_frame, text="90.0%")
        self.concrete_hum_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        ttk.Label(concrete_frame, text="Baterija Senzora:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.concrete_bat_label = ttk.Label(concrete_frame, text="100%")
        self.concrete_bat_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
    
    def setup_air_tab(self, parent):
        """Tab za prikaz stanja vazduha"""
        air_frame = ttk.Frame(parent, padding="10")
        parent.add(air_frame, text="Vazduh")
        
        ttk.Label(air_frame, text="Temperatura Vazduha:").grid(row=0, column=0, sticky=tk.W)
        self.air_temp_label = ttk.Label(air_frame, text="25.0°C")
        self.air_temp_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(air_frame, text="Vlažnost Vazduha:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.air_hum_label = ttk.Label(air_frame, text="60.0%")
        self.air_hum_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        ttk.Label(air_frame, text="Baterija Senzora:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.air_bat_label = ttk.Label(air_frame, text="100%")
        self.air_bat_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
    
    def setup_battery_tab(self, parent):
        """Tab za prikaz stanja svih baterija"""
        battery_frame = ttk.Frame(parent, padding="10")
        parent.add(battery_frame, text="Baterije")
        
        # Kreiranje labels za sve baterije
        batteries = ["Senzor Beton", "Senzor Vazduh", "Pumpa", "Grijač"]
        self.battery_labels = []
        
        for i, battery in enumerate(batteries):
            ttk.Label(battery_frame, text=f"{battery}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            label = ttk.Label(battery_frame, text="100%")
            label.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            self.battery_labels.append(label)
    
    def setup_actuator_tab(self, parent):
        """Tab za prikaz stanja aktuatora"""
        actuator_frame = ttk.Frame(parent, padding="10")
        parent.add(actuator_frame, text="Aktuatori")
        
        # Pumpa
        ttk.Label(actuator_frame, text="Pumpa Status:").grid(row=0, column=0, sticky=tk.W)
        self.pump_status_label = ttk.Label(actuator_frame, text="OFF")
        self.pump_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(actuator_frame, text="Pumpa Vreme Rada:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.pump_time_label = ttk.Label(actuator_frame, text="0 min")
        self.pump_time_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # Grijač
        ttk.Label(actuator_frame, text="Grijač Status:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.heater_status_label = ttk.Label(actuator_frame, text="OFF")
        self.heater_status_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        ttk.Label(actuator_frame, text="Grijač Temperatura:").grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        self.heater_temp_label = ttk.Label(actuator_frame, text="25°C")
        self.heater_temp_label.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
    
    def load_initial_state(self):
        """Učitavanje početnog stanja simulacije iz JSON fajlova"""
        # Učitavanje vremena iz SimData/time.json
        try:
            time_data = self.json_manager.load_time()
            if time_data and 'date' in time_data and 'time' in time_data:
                # Novo format sa odvojenim poljima
                self.sim_time.set_current_time_from_json(time_data['date'], time_data['time'])
                print(f"Učitano vreme iz JSON: {time_data['date']} {time_data['time']}")
            elif time_data and 'current_time' in time_data:
                # Kompatibilnost sa starim formatom
                self.sim_time.set_current_time(time_data['current_time'])
                print(f"Učitano vreme (stari format): {time_data['current_time']}")
            else:
                # Kreiranje početnog vremena ako JSON ne postoji
                print("JSON fajl ne postoji, kreiram početno vreme")
                start_time = datetime(2025, 5, 5, 12, 0, 0)
                self.sim_time.set_current_time(start_time.isoformat())
                # Snimanje početnog vremena u JSON
                self._save_initial_time()
        except Exception as e:
            print(f"Greška pri učitavanju vremena: {e}")
            # Fallback na početno vreme
            start_time = datetime(2025, 5, 5, 12, 0, 0)
            self.sim_time.set_current_time(start_time.isoformat())
            self._save_initial_time()
        
        # Učitavanje ostalih stanja ili kreiranje početnih
        self._load_or_create_initial_models()
        
        # Ažuriranje GUI-ja
        self.update_gui()
    
    def _save_initial_time(self):
        """Snimanje početnog vremena u JSON fajl"""
        try:
            time_json = self.sim_time.get_current_time_json()
            time_data = {
                'date': time_json['date'],
                'time': time_json['time'],
                'step_minutes': int(self.step_var.get())
            }
            self.json_manager.save_time(time_data)
            print(f"Snimljeno početno vreme: {time_data['date']} {time_data['time']}")
        except Exception as e:
            print(f"Greška pri snimanju početnog vremena: {e}")
    
    def _load_or_create_initial_models(self):
        """Učitavanje postojećih modela ili kreiranje početnih stanja"""
        # Pokušaj učitavanja postojećih stanja
        concrete_data = self.json_manager.load_concrete()
        air_data = self.json_manager.load_air()
        battery_data = self.json_manager.load_batteries()
        
        # Reset modela
        self.concrete_model.reset()
        self.air_model.reset()
        self.battery_manager.reset()
        self.actuator_model.reset()
        
        # Primena učitanih podataka ako postoje
        if concrete_data:
            self.concrete_model.temperature = concrete_data.get('temperature', 25.0)
            self.concrete_model.humidity = concrete_data.get('humidity', 100.0)
            print(f"Učitano stanje betona: {concrete_data['temperature']}°C, {concrete_data['humidity']}%")
        
        if air_data:
            self.air_model.temperature = air_data.get('temperature', 25.0)
            self.air_model.humidity = air_data.get('humidity', 60.0)
            print(f"Učitano stanje vazduha: {air_data['temperature']}°C, {air_data['humidity']}%")
        
        if battery_data:
            # Učitavanje nivoa baterija za aktuatore
            pump_battery = battery_data.get('pump_battery', 100.0)
            heater_battery = battery_data.get('heater_battery', 100.0)
            # Postavljanje u battery manager (indeksi 2 i 3 su za aktuatore)
            self.battery_manager.battery_levels[2] = pump_battery
            self.battery_manager.battery_levels[3] = heater_battery
            print(f"Učitani nivoi baterija aktuatora: pumpa {pump_battery}%, grijač {heater_battery}%")
        
        # Kreiranje početnih JSON fajlova ako ne postoje
        if not concrete_data or not air_data or not battery_data:
            self.json_manager.create_initial_files()
            print("Kreirani početni JSON fajlovi")
    
    def get_days_since_start(self):
        """Dobijanje broja dana od početka simulacije (5.5.2025 12:00)"""
        start_time = datetime(2025, 5, 5, 12, 0, 0)
        current_time = datetime.fromisoformat(self.sim_time.get_current_time())
        time_diff = current_time - start_time
        return max(0, time_diff.total_seconds() / (24 * 3600))  # Dani kao float
    
    def start_simulation(self):
        """Pokretanje kontinuirane simulacije"""
        if not self.is_running:
            self.is_running = True
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            
            # Pokretanje u novom thread-u
            self.simulation_thread = threading.Thread(target=self.run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
    
    def stop_simulation(self):
        """Zaustavljanje kontinuirane simulacije"""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
    
    def restart_simulation(self):
        """Restart simulacije na početno stanje"""
        # Prvo zaustavi simulaciju ako je pokrenuta
        if self.is_running:
            self.stop_simulation()
        
        # Potvrda od korisnika
        confirm = messagebox.askyesno(
            "Restart Simulacije", 
            "Da li ste sigurni da želite da restartujete simulaciju na početno stanje?\n\n"
            "Ovo će:\n"
            "• Resetovati vreme na 5.5.2025 12:00\n"
            "• Vratiti sve modele na početne vrednosti\n"
            "• Obrisati postojeće JSON fajlove\n"
            "• Kreirati nova početna stanja"
        )
        
        if not confirm:
            return
        
        try:
            # Brisanje postojećih JSON fajlova
            self.json_manager.clear_all_data()
            
            # Reset vremena na početno stanje
            start_time = datetime(2025, 5, 5, 12, 0, 0)
            self.sim_time.reset(start_time.isoformat())
            
            # Reset svih modela
            self.concrete_model.reset()
            self.air_model.reset()
            self.battery_manager.reset()
            self.actuator_model.reset()
            
            # Reset spoljnih uslova
            self.external_temp = 25.0
            self.external_humidity = 60.0
            self.ext_temp_var.set("25.0")
            self.ext_hum_var.set("60.0")
            
            # Reset checkbox-a za loše baterije
            for i in range(4):
                getattr(self, f"bad_battery_{i}").set(False)
            
            # Kreiranje početnih JSON fajlova
            self.json_manager.create_initial_files()
            
            # Ažuriranje GUI-ja
            self.update_gui()
            
            messagebox.showinfo("Restart", "Simulacija je uspešno restartovana na početno stanje!")
            
        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri restart-u simulacije: {str(e)}")
    
    def run_simulation(self):
        """Glavna petlja kontinuirane simulacije"""
        while self.is_running:
            self.single_step()
            time.sleep(1)  # Pauza između koraka
    
    def single_step(self):
        """Izvršavanje jednog koraka simulacije"""
        try:
            # Dobijanje koraka u minutama
            step_minutes = int(self.step_var.get())
            
            print(f"Izvršavam korak simulacije: {step_minutes} minuta")
            
            # Ažuriranje vremena
            old_time = self.sim_time.get_current_time()
            self.sim_time.advance_time(step_minutes)
            new_time = self.sim_time.get_current_time()
            print(f"Vreme ažurirano: {old_time} -> {new_time}")
            
            # Čitanje aktuatorskih komandi
            actuator_commands = self.json_manager.load_actuators()
            
            # Ažuriranje baterija
            self.update_batteries(step_minutes)
            
            # Ažuriranje aktuatora
            self.actuator_model.update(actuator_commands, step_minutes)
            
            # Ažuriranje spoljnih uslova na osnovu vremena dana
            self.update_external_conditions()
            
            # Ažuriranje modela betona sa danima od početka
            pump_effect = self.actuator_model.get_pump_effect()
            heater_effect = self.actuator_model.get_heater_effect()
            days_since_start = self.get_days_since_start()
            self.concrete_model.update(step_minutes, self.external_temp, 
                                     self.external_humidity, pump_effect, heater_effect, days_since_start)
            
            # Ažuriranje modela vazduha
            concrete_state = self.concrete_model.get_state()
            self.air_model.update(step_minutes, self.external_temp, 
                                self.external_humidity, concrete_state, pump_effect)
            
            # Snimanje stanja u JSON fajlove
            self.save_simulation_state()
            
            # Ažuriranje GUI-ja
            self.root.after(0, self.update_gui)
            
        except ValueError:
            messagebox.showerror("Greška", "Neispravna vrednost za korak simulacije!")
        except Exception as e:
            messagebox.showerror("Greška", f"Greška u simulaciji: {str(e)}")
    
    def update_batteries(self, step_minutes):
        """Ažuriranje stanja baterija"""
        # Provera koja baterija je označena kao loša
        bad_batteries = []
        for i in range(4):
            if getattr(self, f"bad_battery_{i}").get():
                bad_batteries.append(i)
        
        self.battery_manager.update(step_minutes, bad_batteries)
    
    def update_external_conditions(self):
        """Ažuriranje spoljnih uslova na osnovu vremena dana sa preciznim 24h ciklusom"""
        current_time = datetime.fromisoformat(self.sim_time.get_current_time())
        hour = current_time.hour
        minute = current_time.minute
        
        # Precizno vreme u satima (sa minutima)
        time_hours = hour + minute / 60.0
        
        # Referentne vrednosti iz GUI-ja (bazne vrednosti za podne - 12:00)
        try:
            base_temp_noon = float(self.ext_temp_var.get())
            base_humidity_noon = float(self.ext_hum_var.get())
        except:
            base_temp_noon = 25.0
            base_humidity_noon = 60.0
        
        # 24-satni ciklus temperature (cosinusoidalna kriva)
        # Maksimum u podne (12h), minimum u ponoć (0h/24h)
        # Formula: base + amplitude * cos(2π * (hour - 12) / 24)
        temp_amplitude = 8.0  # ±8°C od bazne temperature
        temp_angle = 2 * math.pi * (time_hours - 12) / 24
        temp_variation = temp_amplitude * math.cos(temp_angle)
        self.external_temp = base_temp_noon + temp_variation
        
        # 24-satni ciklus vlažnosti (obrnuto od temperature)
        # Minimum u podne (12h), maksimum u ponoć (0h/24h)
        # Formula: base - amplitude * cos(2π * (hour - 12) / 24)
        humidity_amplitude = 25.0  # ±25% od bazne vlažnosti
        humidity_variation = -humidity_amplitude * math.cos(temp_angle)
        self.external_humidity = max(15, min(95, base_humidity_noon + humidity_variation))
    
    def apply_external_conditions(self):
        """Primena novih spoljnih uslova"""
        try:
            self.external_temp = float(self.ext_temp_var.get())
            self.external_humidity = float(self.ext_hum_var.get())
            messagebox.showinfo("Info", "Spoljni uslovi su ažurirani!")
        except ValueError:
            messagebox.showerror("Greška", "Neispravne vrednosti za spoljne uslove!")
    
    def kill_battery(self, battery_index):
        """Ubijanje određene baterije (postavljanje na 0%)"""
        self.battery_manager.kill_battery(battery_index)
        self.update_gui()
        messagebox.showinfo("Info", f"Baterija {battery_index} je ubijena!")
    
    def save_simulation_state(self):
        """Snimanje trenutnog stanja simulacije u JSON fajlove"""
        # Vreme sa odvojenim poljima
        time_json = self.sim_time.get_current_time_json()
        time_data = {
            'date': time_json['date'],
            'time': time_json['time'],
            'step_minutes': int(self.step_var.get())
        }
        self.json_manager.save_time(time_data)
        
        # Beton
        concrete_state = self.concrete_model.get_state()
        concrete_data = {
            'temperature': concrete_state['temperature'],
            'humidity': concrete_state['humidity'],
            'battery_level': self.battery_manager.get_battery_level(0)
        }
        self.json_manager.save_concrete(concrete_data)
        
        # Vazduh
        air_state = self.air_model.get_state()
        air_data = {
            'temperature': air_state['temperature'],
            'humidity': air_state['humidity'],
            'battery_level': self.battery_manager.get_battery_level(1)
        }
        self.json_manager.save_air(air_data)
        
        # Baterije aktuatora
        battery_data = {
            'pump_battery': self.battery_manager.get_battery_level(2),
            'heater_battery': self.battery_manager.get_battery_level(3)
        }
        self.json_manager.save_batteries(battery_data)
    
    def update_gui(self):
        """Ažuriranje GUI elemenata"""
        # Vreme
        current_time = self.sim_time.get_current_time()
        formatted_time = datetime.fromisoformat(current_time).strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=formatted_time)
        
        # Beton
        concrete_state = self.concrete_model.get_state()
        self.concrete_temp_label.config(text=f"{concrete_state['temperature']:.1f}°C")
        self.concrete_hum_label.config(text=f"{concrete_state['humidity']:.1f}%")
        self.concrete_bat_label.config(text=f"{self.battery_manager.get_battery_level(0):.0f}%")
        
        # Vazduh
        air_state = self.air_model.get_state()
        self.air_temp_label.config(text=f"{air_state['temperature']:.1f}°C")
        self.air_hum_label.config(text=f"{air_state['humidity']:.1f}%")
        self.air_bat_label.config(text=f"{self.battery_manager.get_battery_level(1):.0f}%")
        
        # Baterije
        for i, label in enumerate(self.battery_labels):
            battery_level = self.battery_manager.get_battery_level(i)
            label.config(text=f"{battery_level:.0f}%")
        
        # Aktuatori
        actuator_state = self.actuator_model.get_state()
        
        # Pumpa
        pump_status = "ON" if actuator_state['pump_on'] else "OFF"
        self.pump_status_label.config(text=pump_status)
        self.pump_time_label.config(text=f"{actuator_state['pump_time_remaining']:.0f} min")
        
        # Grijač
        heater_status = "ON" if actuator_state['heater_on'] else "OFF"
        self.heater_status_label.config(text=heater_status)
        self.heater_temp_label.config(text=f"{actuator_state['heater_temperature']:.0f}°C")
    
    def run(self):
        """Pokretanje aplikacije"""
        self.root.mainloop()


if __name__ == "__main__":
    app = SimulationApp()
    app.run()