"""
Model aktuatora za simulaciju pumpe i grijača
Upravlja radom aktuatora i njihovim uticajem na sistem
"""

from typing import Dict, Any, Optional


class ActuatorModel:
    """
    Model za simulaciju aktuatora (pumpa i grijač)
    Simulira njihov rad i uticaj na mikro klimu
    """
    
    def __init__(self):
        """Inicijalizacija modela aktuatora"""
        self.reset()
    
    def reset(self):
        """Reset aktuatora na početno stanje"""
        # Stanje pumpe
        self.pump_on = False
        self.pump_time_remaining = 0.0  # minuti
        self.pump_intensity = 1.0  # 0.0 - 1.0
        
        # Stanje grijača
        self.heater_on = False
        self.heater_temperature = 25.0  # °C
        self.heater_intensity = 1.0  # 0.0 - 1.0
        
        # Parametri efikasnosti (lako za menjanje)
        self.pump_max_flow_rate = 10.0  # L/min maksimalni protok
        self.pump_cooling_efficiency = 0.8  # Efikasnost hlađenja
        self.pump_humidifying_efficiency = 0.9  # Efikasnost povećanja vlažnosti
        
        self.heater_max_power = 2000.0  # W maksimalna snaga
        self.heater_heating_efficiency = 0.85  # Efikasnost zagrevanja
        self.heater_water_capacity = 50.0  # L kapacitet rezervoara
        
        # Trenutno stanje vode u sistemu
        self.water_temperature = 25.0  # °C temperatura vode
        self.water_level = 100.0  # % nivo vode u rezervoaru
    
    def update(self, commands: Optional[Dict[str, Any]], step_minutes: int):
        """
        Ažuriranje stanja aktuatora na osnovu komandi
        
        Args:
            commands (Optional[Dict[str, Any]]): Komande za aktuatore
            step_minutes (int): Broj minuta koji je prošao
        """
        if commands is None:
            commands = {}
        
        # Ažuriranje pumpe
        self._update_pump(commands.get('pump', {}), step_minutes)
        
        # Ažuriranje grijača
        self._update_heater(commands.get('heater', {}), step_minutes)
        
        # Ažuriranje vode u sistemu
        self._update_water_system(step_minutes)
    
    def _update_pump(self, pump_commands: Dict[str, Any], step_minutes: int):
        """
        Ažuriranje stanja pumpe
        
        Args:
            pump_commands (Dict[str, Any]): Komande za pumpu
            step_minutes (int): Broj minuta
        """
        # Čitanje komandi
        status = pump_commands.get('status', 0)
        runtime_minutes = pump_commands.get('runtime_minutes', 0)
        
        # Postavljanje novog stanja ako je komanda za uključivanje
        if status == 1 and not self.pump_on:
            self.pump_on = True
            self.pump_time_remaining = float(runtime_minutes)
        elif status == 0:
            self.pump_on = False
            self.pump_time_remaining = 0.0
        
        # Ažuriranje vremena rada
        if self.pump_on and self.pump_time_remaining > 0:
            if self.pump_time_remaining <= step_minutes:
                # Pumpa se isključuje tokom ovog koraka
                effective_runtime = self.pump_time_remaining
                self.pump_time_remaining = 0.0
                self.pump_on = False
            else:
                # Pumpa nastavlja da radi
                effective_runtime = step_minutes
                self.pump_time_remaining -= step_minutes
        else:
            effective_runtime = 0.0
            self.pump_on = False
        
        # Ažuriranje intenziteta na osnovu dostupnosti vode i energije
        self.pump_intensity = self._calculate_pump_intensity()
        
        # Potrošnja vode ako pumpa radi
        if effective_runtime > 0:
            water_consumption = self._calculate_water_consumption(effective_runtime)
            self.water_level = max(0, self.water_level - water_consumption)
    
    def _update_heater(self, heater_commands: Dict[str, Any], step_minutes: int):
        """
        Ažuriranje stanja grijača
        
        Args:
            heater_commands (Dict[str, Any]): Komande za grijač
            step_minutes (int): Broj minuta
        """
        # Čitanje komandi
        status = heater_commands.get('status', 0)
        target_temperature = heater_commands.get('temperature', 25.0)
        
        # Postavljanje stanja
        self.heater_on = (status == 1)
        self.heater_temperature = float(target_temperature)
        
        # Ažuriranje intenziteta
        self.heater_intensity = self._calculate_heater_intensity()
        
        # Zagrevanje vode ako grijač radi
        if self.heater_on:
            self._heat_water(step_minutes)
    
    def _update_water_system(self, step_minutes: int):
        """
        Ažuriranje sistema vode
        
        Args:
            step_minutes (int): Broj minuta
        """
        # Prirodno hlađenje vode
        step_hours = step_minutes / 60.0
        ambient_temp = 25.0  # Ambijentalna temperatura
        
        # Newtonov zakon hlađenja
        cooling_rate = 0.02  # Konstanta hlađenja
        temp_diff = self.water_temperature - ambient_temp
        cooling = temp_diff * cooling_rate * step_hours * 60
        
        self.water_temperature -= cooling
        self.water_temperature = max(ambient_temp, self.water_temperature)
        
        # Prirodno dopunjavanje vode (simulacija automatskog sistema)
        if self.water_level < 95:
            refill_rate = 2.0  # % po satu
            refill = refill_rate * step_hours
            self.water_level = min(100, self.water_level + refill)
    
    def _calculate_pump_intensity(self) -> float:
        """
        Računanje intenziteta pumpe na osnovu dostupnih resursa
        
        Returns:
            float: Intenzitet pumpe (0.0 - 1.0)
        """
        # Intenzitet zavisi od nivoa vode
        if self.water_level <= 0:
            return 0.0
        elif self.water_level < 20:
            return 0.3  # Smanjen rad zbog malo vode
        elif self.water_level < 50:
            return 0.7  # Umeren rad
        else:
            return 1.0  # Pun rad
    
    def _calculate_heater_intensity(self) -> float:
        """
        Računanje intenziteta grijača
        
        Returns:
            float: Intenzitet grijača (0.0 - 1.0)
        """
        if not self.heater_on:
            return 0.0
        
        # Intenzitet zavisi od razlike između trenutne i ciljne temperature
        temp_diff = abs(self.heater_temperature - self.water_temperature)
        
        if temp_diff > 20:
            return 1.0  # Maksimalan rad
        elif temp_diff > 10:
            return 0.8  # Visok rad
        elif temp_diff > 5:
            return 0.5  # Umeren rad
        else:
            return 0.2  # Održavanje temperature
    
    def _calculate_water_consumption(self, runtime_minutes: float) -> float:
        """
        Računanje potrošnje vode
        
        Args:
            runtime_minutes (float): Vreme rada u minutima
            
        Returns:
            float: Potrošnja vode u %
        """
        # Potrošnja zavisi od protoka i intenziteta
        flow_rate = self.pump_max_flow_rate * self.pump_intensity  # L/min
        total_consumption = flow_rate * runtime_minutes  # L
        
        # Konverzija u procente rezervoara
        consumption_percent = (total_consumption / self.heater_water_capacity) * 100
        return consumption_percent
    
    def _heat_water(self, step_minutes: int):
        """
        Zagrevanje vode grijačem
        
        Args:
            step_minutes (int): Broj minuta
        """
        if not self.heater_on:
            return
        
        step_hours = step_minutes / 60.0
        target_temp = self.heater_temperature
        current_temp = self.water_temperature
        
        # Brzina zagrevanja zavisi od snage i intenziteta
        heating_power = self.heater_max_power * self.heater_intensity  # W
        heating_rate = heating_power / 1000.0  # °C po satu (aproksimacija)
        
        # Računanje zagrevanja
        if current_temp < target_temp:
            temp_increase = heating_rate * step_hours * self.heater_heating_efficiency
            self.water_temperature = min(target_temp, current_temp + temp_increase)
    
    def get_pump_effect(self) -> Dict[str, Any]:
        """
        Dobijanje efekata pumpe na sistem
        
        Returns:
            Dict[str, Any]: Efekti pumpe
        """
        if not self.pump_on or self.pump_intensity <= 0:
            return {
                'active': False,
                'intensity': 0.0,
                'cooling_effect': 0.0,
                'humidifying_effect': 0.0,
                'water_temperature': self.water_temperature
            }
        
        # Efekti zavise od intenziteta i temperature vode
        base_cooling = 5.0  # °C osnovnog hlađenja
        base_humidifying = 20.0  # % osnovnog povećanja vlažnosti
        
        # Temperatura vode utiče na efekat
        temp_factor = max(0.1, (self.water_temperature - 10) / 40)  # 0.1 - 1.0
        
        cooling_effect = base_cooling * self.pump_intensity * self.pump_cooling_efficiency
        humidifying_effect = base_humidifying * self.pump_intensity * self.pump_humidifying_efficiency
        
        # Hladnija voda = bolji efekat hlađenja
        if self.water_temperature < 20:
            cooling_effect *= 1.5
        
        return {
            'active': True,
            'intensity': self.pump_intensity,
            'cooling_effect': cooling_effect,
            'humidifying_effect': humidifying_effect,
            'water_temperature': self.water_temperature,
            'flow_rate': self.pump_max_flow_rate * self.pump_intensity
        }
    
    def get_heater_effect(self) -> Dict[str, Any]:
        """
        Dobijanje efekata grijača na sistem
        
        Returns:
            Dict[str, Any]: Efekti grijača
        """
        if not self.heater_on:
            return {
                'active': False,
                'intensity': 0.0,
                'heating_effect': 0.0,
                'temperature': self.heater_temperature,
                'water_temperature': self.water_temperature
            }
        
        # Efekti grijača zavise od intenziteta
        base_heating = 10.0  # °C osnovnog zagrevanja
        heating_effect = base_heating * self.heater_intensity * self.heater_heating_efficiency
        
        return {
            'active': True,
            'intensity': self.heater_intensity,
            'heating_effect': heating_effect,
            'temperature': self.heater_temperature,
            'water_temperature': self.water_temperature,
            'power_consumption': self.heater_max_power * self.heater_intensity
        }
    
    def get_state(self) -> Dict[str, Any]:
        """
        Dobijanje trenutnog stanja aktuatora
        
        Returns:
            Dict[str, Any]: Trenutno stanje
        """
        return {
            'pump_on': self.pump_on,
            'pump_time_remaining': round(self.pump_time_remaining, 1),
            'pump_intensity': round(self.pump_intensity, 2),
            'heater_on': self.heater_on,
            'heater_temperature': round(self.heater_temperature, 1),
            'heater_intensity': round(self.heater_intensity, 2),
            'water_temperature': round(self.water_temperature, 1),
            'water_level': round(self.water_level, 1)
        }
    
    def get_detailed_state(self) -> Dict[str, Any]:
        """
        Dobijanje detaljnog stanja aktuatora
        
        Returns:
            Dict[str, Any]: Detaljno stanje
        """
        state = self.get_state()
        
        # Dodavanje dodatnih informacija
        state.update({
            'pump_status_text': self._get_pump_status_text(),
            'heater_status_text': self._get_heater_status_text(),
            'water_system_status': self._get_water_system_status(),
            'energy_consumption': self._calculate_energy_consumption()
        })
        
        return state
    
    def _get_pump_status_text(self) -> str:
        """
        Tekstualni opis stanja pumpe
        
        Returns:
            str: Status pumpe
        """
        if not self.pump_on:
            return "Isključena"
        elif self.pump_intensity > 0.8:
            return f"Pun rad - {self.pump_time_remaining:.0f} min preostalo"
        elif self.pump_intensity > 0.5:
            return f"Umeren rad - {self.pump_time_remaining:.0f} min preostalo"
        else:
            return f"Smanjen rad - {self.pump_time_remaining:.0f} min preostalo"
    
    def _get_heater_status_text(self) -> str:
        """
        Tekstualni opis stanja grijača
        
        Returns:
            str: Status grijača
        """
        if not self.heater_on:
            return "Isključen"
        elif self.water_temperature >= self.heater_temperature - 1:
            return f"Održava temperaturu {self.heater_temperature:.0f}°C"
        else:
            return f"Grije do {self.heater_temperature:.0f}°C"
    
    def _get_water_system_status(self) -> str:
        """
        Opis stanja sistema vode
        
        Returns:
            str: Status vode
        """
        if self.water_level < 20:
            return "Nizak nivo vode"
        elif self.water_level < 50:
            return "Umeren nivo vode"
        else:
            return "Dovoljan nivo vode"
    
    def _calculate_energy_consumption(self) -> Dict[str, float]:
        """
        Računanje potrošnje energije
        
        Returns:
            Dict[str, float]: Potrošnja energije
        """
        pump_power = 200.0 if self.pump_on else 0.0  # W
        heater_power = self.heater_max_power * self.heater_intensity if self.heater_on else 0.0
        
        return {
            'pump_power': pump_power,
            'heater_power': heater_power,
            'total_power': pump_power + heater_power
        }