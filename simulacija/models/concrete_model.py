"""
Model betona za simulaciju betonske deke
Simulira temperaturu i vlažnost betona sa uticajem spoljnih faktora
"""

import math
from typing import Dict, Any


class ConcreteModel:
    """
    Model za simulaciju betonske deke
    Simulira temperaturu i vlažnost sa realističkim fizičkim zavisnostima
    """
    
    def __init__(self):
        """Inicijalizacija modela betona"""
        self.reset()
    
    def reset(self):
        """Reset modela na početno stanje"""
        # Početne vrednosti
        self.temperature = 25.0  # °C
        self.humidity = 100.0    # % - maksimalna vlažnost pri izljevanju (početak)
        
        # Fizički parametri betona (lako za menjanje)
        self.thermal_mass = 0.95  # Termalna masa - beton sporije menja temperaturu
        
        # Sistem sušenja deke tokom 7 dana
        self.drying_duration_days = 7.0  # Dani za potpuno sušenje
        self.initial_humidity = 100.0    # Početna vlažnost pri izljevanju
        self.final_humidity = 25.0       # Finalna vlažnost nakon 7 dana
        
        # Faktori za uticaj spoljnih uslova
        self.external_temp_influence = 0.01   # Koliko spoljnja temp. utiče po minuti
        self.external_humidity_influence = 0.005  # Koliko spoljna vlažnost utiče
        
        # Parametri za uticaj pumpe
        self.pump_cooling_effect = 4.0    # °C hlađenja kada pumpa radi
        self.pump_humidity_effect = 20.0  # % povećanja vlažnosti
        
        # Parametri za uticaj grijača
        self.heater_warming_effect = 10.0  # °C zagrevanja
        self.heater_drying_effect = 5.0    # % smanjenja vlažnosti
    
    def update(self, step_minutes: int, external_temp: float, external_humidity: float,
               pump_effect: Dict[str, Any], heater_effect: Dict[str, Any], days_since_start: float = 0.0):
        """
        Ažuriranje stanja betona
        
        Args:
            step_minutes (int): Broj minuta koji je prošao
            external_temp (float): Spoljna temperatura (°C)
            external_humidity (float): Spoljna vlažnost (%)
            pump_effect (Dict[str, Any]): Efekat pumpe
            heater_effect (Dict[str, Any]): Efekat grijača
            days_since_start (float): Broj dana od početka simulacije
        """
        # Konvertovanje u sate za lakše računanje
        step_hours = step_minutes / 60.0
        
        # Ažuriranje temperature
        self._update_temperature(step_hours, external_temp, pump_effect, heater_effect)
        
        # Ažuriranje vlažnosti sa novim sistemom sušenja
        self._update_humidity_with_drying(step_hours, external_humidity, pump_effect, 
                                         heater_effect, days_since_start)
        
        # Ograničavanje vrednosti
        self.temperature = max(-10, min(60, self.temperature))  # Realne granice
        self.humidity = max(self.final_humidity, min(100, self.humidity))
    
    def _update_temperature(self, step_hours: float, external_temp: float,
                           pump_effect: Dict[str, Any], heater_effect: Dict[str, Any]):
        """
        Ažuriranje temperature betona
        
        Args:
            step_hours (float): Broj sati koji je prošao
            external_temp (float): Spoljna temperatura
            pump_effect (Dict[str, Any]): Efekat pumpe
            heater_effect (Dict[str, Any]): Efekat grijača
        """
        # Spoljni uticaj (beton sporije menja temperaturu zbog termalne mase)
        temp_diff = external_temp - self.temperature
        external_change = temp_diff * self.external_temp_influence * step_hours * 60
        external_change *= self.thermal_mass  # Termalna masa usporava promene
        
        # Efekat pumpe (hlađenje)
        pump_change = 0.0
        if pump_effect.get('active', False):
            intensity = pump_effect.get('intensity', 1.0)
            pump_change = -self.pump_cooling_effect * intensity * step_hours
        
        # Efekat grijača (zagrevanje)
        heater_change = 0.0
        if heater_effect.get('active', False):
            target_temp = heater_effect.get('temperature', 25.0)
            intensity = heater_effect.get('intensity', 1.0)
            
            # Grijač greje vodu koja zatim utiče na beton
            if target_temp > self.temperature:
                heater_change = self.heater_warming_effect * intensity * step_hours
        
        # Prirodno hlađenje/zagrevanje (fizička svojstva betona)
        natural_change = self._calculate_natural_temperature_change(step_hours)
        
        # Ukupna promena temperature
        total_change = external_change + pump_change + heater_change + natural_change
        self.temperature += total_change
    
    def _calculate_natural_temperature_change(self, step_hours: float) -> float:
        """
        Prirodna promena temperature zbog fizičkih svojstava betona
        
        Args:
            step_hours (float): Broj sati
            
        Returns:
            float: Promena temperature
        """
        # Beton polako oslobađa toplotu tokom stvrdnjavanja (prvi dani)
        # Ova toplota se vremenom smanjuje
        hydration_heat = 0.5 * step_hours * math.exp(-0.1 * step_hours)
        return hydration_heat
    
    def _update_humidity_with_drying(self, step_hours: float, external_humidity: float,
                                    pump_effect: Dict[str, Any], heater_effect: Dict[str, Any], 
                                    days_since_start: float):
        """
        Ažuriranje vlažnosti betona sa novim sistemom prirodnog sušenja deke
        
        Args:
            step_hours (float): Broj sati koji je prošao
            external_humidity (float): Spoljna vlažnost
            pump_effect (Dict[str, Any]): Efekat pumpe
            heater_effect (Dict[str, Any]): Efekat grijača
            days_since_start (float): Broj dana od početka simulacije
        """
        # Prirodno sušenje deke tokom 7 dana (eksponencijalna kriva)
        natural_drying_rate = self._calculate_drying_rate(days_since_start)
        natural_drying = natural_drying_rate * step_hours * 60  # Po minuti
        
        # Uticaj temperature na sušenje (viša temperatura = brže sušenje)
        temp_factor = max(0.5, (self.temperature - 10) / 30)  # 0.5 - 1.67 faktor
        temp_enhanced_drying = natural_drying * temp_factor
        
        # Uticaj spoljnje vlažnosti (ograničen)
        humidity_diff = external_humidity - self.humidity
        external_change = humidity_diff * self.external_humidity_influence * step_hours * 60
        external_change = max(-2, min(2, external_change))  # Ograniči na ±2% po satu
        
        # Efekat pumpe (povećanje vlažnosti)
        pump_change = 0.0
        if pump_effect.get('active', False):
            intensity = pump_effect.get('intensity', 1.0)
            pump_change = self.pump_humidity_effect * intensity * step_hours
        
        # Efekat grijača (smanjenje vlažnosti)
        heater_change = 0.0
        if heater_effect.get('active', False):
            intensity = heater_effect.get('intensity', 1.0)
            heater_change = -self.heater_drying_effect * intensity * step_hours
        
        # Ukupna promena vlažnosti
        total_change = (-temp_enhanced_drying + external_change + pump_change + heater_change)
        
        self.humidity += total_change
    
    def _calculate_drying_rate(self, days_since_start: float) -> float:
        """
        Računanje brzine prirodnog sušenja deke na osnovu vremena
        
        Args:
            days_since_start (float): Broj dana od početka simulacije
            
        Returns:
            float: Brzina sušenja (% vlažnosti po satu)
        """
        if days_since_start >= self.drying_duration_days:
            return 0.0  # Potpuno osušena nakon 7 dana
        
        # Eksponencijalna kriva sušenja - brže na početku, sporije na kraju
        # Formula: max_rate * e^(-k * days) gde je k = 2/7 za 90% sušenja za 7 dana
        k = 2.0 / self.drying_duration_days  # Konstanta eksponencijalnog opadanja
        max_rate = 2.5  # Maksimalna brzina sušenja na početku (% po satu)
        
        drying_rate = max_rate * math.exp(-k * days_since_start)
        
        # Dodatni faktor na osnovu trenutne vlažnosti
        humidity_factor = (self.humidity - self.final_humidity) / (self.initial_humidity - self.final_humidity)
        humidity_factor = max(0.0, min(1.0, humidity_factor))
        
        return drying_rate * humidity_factor
    
    def get_state(self) -> Dict[str, float]:
        """
        Dobijanje trenutnog stanja betona
        
        Returns:
            Dict[str, float]: Trenutno stanje
        """
        return {
            'temperature': round(self.temperature, 2),
            'humidity': round(self.humidity, 2)
        }
    
    def get_detailed_state(self) -> Dict[str, Any]:
        """
        Dobijanje detaljnog stanja betona
        
        Returns:
            Dict[str, Any]: Detaljno stanje sa dodatnim informacijama
        """
        return {
            'temperature': round(self.temperature, 2),
            'humidity': round(self.humidity, 2),
            'state_description': self._get_state_description(),
            'drying_rate': self._calculate_current_drying_rate(),
            'thermal_condition': self._get_thermal_condition()
        }
    
    def _get_state_description(self) -> str:
        """
        Tekstualni opis stanja betona
        
        Returns:
            str: Opis stanja
        """
        if self.humidity > 80:
            return "Vrlo vlažan - početna faza"
        elif self.humidity > 60:
            return "Umereno vlažan - sušenje u toku"
        elif self.humidity > 40:
            return "Suv - napredna faza"
        elif self.humidity > 25:
            return "Vrlo suv - skoro gotov"
        else:
            return "Potpuno suv - završena faza"
    
    def _calculate_current_drying_rate(self) -> float:
        """
        Računanje trenutne brzine sušenja
        
        Returns:
            float: Brzina sušenja (% vlažnosti po satu)
        """
        base_rate = self.humidity_decay_base * 60  # Po satu
        temp_factor = max(0, self.temperature - 20) * self.humidity_temp_factor * 60
        return base_rate + temp_factor
    
    def _get_thermal_condition(self) -> str:
        """
        Opis termalne situacije
        
        Returns:
            str: Termalnie stanje
        """
        if self.temperature < 10:
            return "Hladno - sporije stvrdnjavanje"
        elif self.temperature < 20:
            return "Umeren - normalno stvrdnjavanje"
        elif self.temperature < 30:
            return "Toplo - ubrzano stvrdnjavanje"
        elif self.temperature < 40:
            return "Vrlo toplo - brže sušenje"
        else:
            return "Pretopl - mogući problemi"
    
    def apply_external_shock(self, temp_change: float, humidity_change: float):
        """
        Primena spoljašnjeg šoka (npr. kiša, vetar)
        
        Args:
            temp_change (float): Promena temperature
            humidity_change (float): Promena vlažnosti
        """
        self.temperature += temp_change
        self.humidity += humidity_change
        
        # Ograničavanje vrednosti
        self.temperature = max(-10, min(60, self.temperature))
        self.humidity = max(self.min_humidity, min(100, self.humidity))
    
    def get_curing_progress(self) -> float:
        """
        Dobijanje progresa stvrdnjavanja betona (0.0 - 1.0)
        Na osnovu vlažnosti i temperature
        
        Returns:
            float: Progress stvrdnjavanja
        """
        # Inverzna funkcija vlažnosti (manja vlažnost = veći progress)
        humidity_progress = (90 - self.humidity) / (90 - self.min_humidity)
        humidity_progress = max(0.0, min(1.0, humidity_progress))
        
        # Faktor temperature (optimalna oko 20-25°C)
        if 15 <= self.temperature <= 30:
            temp_factor = 1.0
        elif self.temperature < 15:
            temp_factor = 0.5 + (self.temperature / 30)
        else:
            temp_factor = max(0.3, 1.0 - (self.temperature - 30) / 30)
        
        return humidity_progress * temp_factor