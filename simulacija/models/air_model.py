"""
Model vazduha za simulaciju mikro klime iznad betonske deke
Simulira temperaturu i vlažnost vazduha sa interakcijom sa betonom
"""

import math
from typing import Dict, Any


class AirModel:
    """
    Model za simulaciju vazduha iznad betonske deke
    Simulira mikro klimu sa dnevnim ciklusom i uticajem betona
    """
    
    def __init__(self):
        """Inicijalizacija modela vazduha"""
        self.reset()
    
    def reset(self):
        """Reset modela na početno stanje"""
        # Početne vrednosti
        self.temperature = 25.0  # °C
        self.humidity = 60.0     # % - umerena početna vlažnost
        
        # Fizički parametri vazduha (lako za menjanje)
        self.thermal_responsiveness = 0.6  # Vazduh brže menja temperaturu od betona (umanjeno)
        self.humidity_exchange_rate = 0.015  # Brzina razmene vlažnosti sa okruženjem (smanjena)
        self.concrete_influence_factor = 0.25  # Koliko beton utiče na vazduh (smanjeno)
        
        # Dnevni ciklus parametri (umanjeni)
        self.daily_temp_variation = 8.0  # °C maksimalne dnevne varijacije
        self.daily_humidity_variation = 20.0  # % maksimalne dnevne varijacije
        
        # Faktori uticaja aktuatora (uravnoteženi)
        self.pump_air_cooling = 1.5      # °C hlađenja vazduha kada pumpa radi
        self.pump_air_humidifying = 10.0  # % povećanja vlažnosti vazduha
        self.air_circulation_factor = 1.3  # Pojačavanje efekata zbog cirkulacije
        
        # Parametri za interakciju sa betonom (smanjeni)
        self.concrete_temp_transfer = 0.08   # Brzina prenosa toplote sa betona
        self.concrete_humidity_transfer = 0.04  # Brzina prenosa vlažnosti
        
        # Minimalne i maksimalne vrednosti
        self.min_humidity = 10.0  # %
        self.max_humidity = 95.0  # %
    
    def update(self, step_minutes: int, external_temp: float, external_humidity: float,
               concrete_state: Dict[str, float], pump_effect: Dict[str, Any]):
        """
        Ažuriranje stanja vazduha
        
        Args:
            step_minutes (int): Broj minuta koji je prošao
            external_temp (float): Spoljna temperatura (°C)
            external_humidity (float): Spoljna vlažnost (%)
            concrete_state (Dict[str, float]): Stanje betona
            pump_effect (Dict[str, Any]): Efekat pumpe
        """
        step_hours = step_minutes / 60.0
        
        # Ažuriranje temperature
        self._update_temperature(step_hours, external_temp, concrete_state, pump_effect)
        
        # Ažuriranje vlažnosti
        self._update_humidity(step_hours, external_humidity, concrete_state, pump_effect)
        
        # Ograničavanje vrednosti
        self.temperature = max(-20, min(50, self.temperature))
        self.humidity = max(self.min_humidity, min(self.max_humidity, self.humidity))
    
    def _update_temperature(self, step_hours: float, external_temp: float,
                           concrete_state: Dict[str, float], pump_effect: Dict[str, Any]):
        """
        Ažuriranje temperature vazduha
        
        Args:
            step_hours (float): Broj sati koji je prošao
            external_temp (float): Spoljna temperatura
            concrete_state (Dict[str, float]): Stanje betona
            pump_effect (Dict[str, Any]): Efekat pumpe
        """
        # Spoljni uticaj (vazduh brže reaguje od betona)
        temp_diff = external_temp - self.temperature
        external_change = temp_diff * self.thermal_responsiveness * 0.1 * step_hours * 60
        
        # Poboljšana interakcija sa betonom - temperaturni transfer
        concrete_temp = concrete_state.get('temperature', 25.0)
        concrete_temp_diff = concrete_temp - self.temperature
        
        # Intenzitet prenosa zavisi od razlike temperatura
        temp_transfer_intensity = min(1.0, abs(concrete_temp_diff) / 10.0)
        concrete_temp_change = (concrete_temp_diff * self.concrete_temp_transfer * 
                               self.concrete_influence_factor * temp_transfer_intensity * 
                               step_hours * 60)
        
        # Efekat pumpe (hlađenje vazduha)
        pump_change = 0.0
        if pump_effect.get('active', False):
            intensity = pump_effect.get('intensity', 1.0)
            pump_change = -self.pump_air_cooling * intensity * step_hours
            
            # Pojačavanje zbog cirkulacije vazduha
            pump_change *= self.air_circulation_factor
        
        # Mikro klimatski efekti
        microclimate_change = self._calculate_microclimate_temperature_effect(step_hours)
        
        # Ukupna promena temperature
        total_temp_change = external_change + concrete_temp_change + pump_change + microclimate_change
        self.temperature += total_temp_change
    
    def _update_humidity(self, step_hours: float, external_humidity: float,
                        concrete_state: Dict[str, float], pump_effect: Dict[str, Any]):
        """
        Ažuriranje vlažnosti vazduha
        
        Args:
            step_hours (float): Broj sati koji je prošao
            external_humidity (float): Spoljna vlažnost
            concrete_state (Dict[str, float]): Stanje betona
            pump_effect (Dict[str, Any]): Efekat pumpe
        """
        # Spoljni uticaj (prirodna ventilacija)
        humidity_diff = external_humidity - self.humidity
        external_change = humidity_diff * self.humidity_exchange_rate * step_hours * 60
        
        # Poboljšana interakcija vlažnosti sa betonom
        concrete_humidity = concrete_state.get('humidity', 60.0)
        humidity_diff = concrete_humidity - self.humidity
        
        # Intenzitet prenosa zavisi od razlike vlažnosti i temperature
        humidity_transfer_intensity = min(1.0, abs(humidity_diff) / 20.0)
        temp_boost = 1.0 + (max(0, self.temperature - 20) / 30.0)  # Viša temp = brži transfer
        
        if humidity_diff > 0:
            # Beton oslobađa vlažnost u vazduh
            concrete_humidity_change = (humidity_diff * self.concrete_humidity_transfer * 
                                       self.concrete_influence_factor * humidity_transfer_intensity * 
                                       temp_boost * step_hours * 60)
        else:
            # Vazduh može da suši beton (sporije)
            concrete_humidity_change = (humidity_diff * self.concrete_humidity_transfer * 
                                       0.3 * humidity_transfer_intensity * step_hours * 60)
        
        # Efekat pumpe (povećanje vlažnosti)
        pump_change = 0.0
        if pump_effect.get('active', False):
            intensity = pump_effect.get('intensity', 1.0)
            pump_change = self.pump_air_humidifying * intensity * step_hours
            
            # Pojačavanje zbog cirkulacije
            pump_change *= self.air_circulation_factor
        
        # Prirodno sušenje vazduha (evaporacija)
        evaporation_change = self._calculate_evaporation_effect(step_hours)
        
        # Ukupna promena vlažnosti
        total_humidity_change = external_change + concrete_humidity_change + pump_change + evaporation_change
        self.humidity += total_humidity_change
    
    def _calculate_microclimate_temperature_effect(self, step_hours: float) -> float:
        """
        Računanje mikro klimatskih efekata na temperaturu
        
        Args:
            step_hours (float): Broj sati
            
        Returns:
            float: Promena temperature zbog mikro klime
        """
        # Efekat "toplotnog ostrva" iznad betona
        # Beton zadržava toplotu i stvara mikro klimu
        if self.temperature > 25:
            heat_island_effect = 0.5 * step_hours * math.log(1 + (self.temperature - 25) / 10)
            return heat_island_effect
        return 0.0
    
    def _calculate_evaporation_effect(self, step_hours: float) -> float:
        """
        Računanje efekta evaporacije na vlažnost
        
        Args:
            step_hours (float): Broj sati
            
        Returns:
            float: Promena vlažnosti zbog evaporacije
        """
        # Evaporacija zavisi od temperature i trenutne vlažnosti
        if self.temperature > 20 and self.humidity > 30:
            evaporation_rate = 0.5 * step_hours * (self.temperature - 20) / 20
            evaporation_rate *= (self.humidity / 100.0)  # Proporcionalno vlažnosti
            return -evaporation_rate
        return 0.0
    
    def apply_daily_cycle(self, hour_of_day: int):
        """
        Primena dnevnog ciklusa na temperaturu i vlažnost
        
        Args:
            hour_of_day (int): Sat u danu (0-23)
        """
        # Temperatura: minimum u 6h ujutru, maksimum u 14h
        temp_cycle_factor = math.sin((hour_of_day - 6) * math.pi / 12)
        daily_temp_effect = self.daily_temp_variation * temp_cycle_factor * 0.1
        
        # Vlažnost: obrnuto od temperature
        humidity_cycle_factor = -math.sin((hour_of_day - 6) * math.pi / 12)
        daily_humidity_effect = self.daily_humidity_variation * humidity_cycle_factor * 0.1
        
        self.temperature += daily_temp_effect
        self.humidity += daily_humidity_effect
    
    def get_state(self) -> Dict[str, float]:
        """
        Dobijanje trenutnog stanja vazduha
        
        Returns:
            Dict[str, float]: Trenutno stanje
        """
        return {
            'temperature': round(self.temperature, 2),
            'humidity': round(self.humidity, 2)
        }
    
    def get_detailed_state(self) -> Dict[str, Any]:
        """
        Dobijanje detaljnog stanja vazduha
        
        Returns:
            Dict[str, Any]: Detaljno stanje sa dodatnim informacijama
        """
        return {
            'temperature': round(self.temperature, 2),
            'humidity': round(self.humidity, 2),
            'comfort_index': self._calculate_comfort_index(),
            'air_quality': self._get_air_quality_description(),
            'microclimate_status': self._get_microclimate_status()
        }
    
    def _calculate_comfort_index(self) -> float:
        """
        Računanje indeksa komfora (0.0 - 1.0)
        Na osnovu temperature i vlažnosti
        
        Returns:
            float: Indeks komfora
        """
        # Optimalne vrednosti: 20-25°C, 40-60% vlažnosti
        temp_comfort = 1.0 - abs(self.temperature - 22.5) / 22.5
        temp_comfort = max(0.0, temp_comfort)
        
        humidity_comfort = 1.0 - abs(self.humidity - 50) / 50
        humidity_comfort = max(0.0, humidity_comfort)
        
        return (temp_comfort + humidity_comfort) / 2
    
    def _get_air_quality_description(self) -> str:
        """
        Tekstualni opis kvaliteta vazduha
        
        Returns:
            str: Opis kvaliteta vazduha
        """
        comfort = self._calculate_comfort_index()
        
        if comfort > 0.8:
            return "Odličan"
        elif comfort > 0.6:
            return "Dobar"
        elif comfort > 0.4:
            return "Umeren"
        elif comfort > 0.2:
            return "Loš"
        else:
            return "Vrlo loš"
    
    def _get_microclimate_status(self) -> str:
        """
        Opis stanja mikro klime
        
        Returns:
            str: Status mikro klime
        """
        if self.temperature > 30 and self.humidity > 70:
            return "Toplo i vlažno - intenzivna mikro klima"
        elif self.temperature > 25 and self.humidity < 40:
            return "Toplo i suvo - aridna mikro klima"
        elif self.temperature < 15 and self.humidity > 80:
            return "Hladno i vlažno - kondenzacija moguća"
        elif 20 <= self.temperature <= 25 and 40 <= self.humidity <= 60:
            return "Optimalna mikro klima"
        else:
            return "Varijabilna mikro klima"
    
    def calculate_interaction_with_concrete(self, concrete_state: Dict[str, float]) -> Dict[str, float]:
        """
        Računanje interakcije sa betonom
        
        Args:
            concrete_state (Dict[str, float]): Stanje betona
            
        Returns:
            Dict[str, float]: Efekti interakcije
        """
        concrete_temp = concrete_state.get('temperature', 25.0)
        concrete_humidity = concrete_state.get('humidity', 60.0)
        
        # Temperaturna razmena
        temp_exchange = (concrete_temp - self.temperature) * self.concrete_temp_transfer
        
        # Razmena vlažnosti
        humidity_exchange = (concrete_humidity - self.humidity) * self.concrete_humidity_transfer
        
        return {
            'temperature_exchange': temp_exchange,
            'humidity_exchange': humidity_exchange,
            'thermal_gradient': abs(concrete_temp - self.temperature),
            'humidity_gradient': abs(concrete_humidity - self.humidity)
        }
    
    def get_wind_simulation(self, pump_active: bool) -> Dict[str, Any]:
        """
        Simulacija vetra/cirkulacije vazduha
        
        Args:
            pump_active (bool): Da li pumpa radi (stvara cirkulaciju)
            
        Returns:
            Dict[str, Any]: Informacije o cirkulaciji vazduha
        """
        base_circulation = 0.2  # Prirodna cirkulacija
        
        if pump_active:
            circulation_strength = base_circulation * self.air_circulation_factor
            circulation_type = "Veštačka cirkulacija (pumpa)"
        else:
            circulation_strength = base_circulation
            circulation_type = "Prirodna cirkulacija"
        
        return {
            'circulation_strength': circulation_strength,
            'circulation_type': circulation_type,
            'cooling_effect': circulation_strength * 2,
            'drying_effect': circulation_strength * 3
        }