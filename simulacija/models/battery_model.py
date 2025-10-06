"""
Model baterija za simulaciju IoT uređaja
Simulira baterije za senzore i aktuatore sa različitim režimima rada
"""

from typing import List, Dict


class BatteryManager:
    """
    Manager za upravljanje svim baterijama u simulaciji
    Simulira 4 baterije: 2 za senzore + 2 za aktuatore
    """
    
    def __init__(self):
        """Inicijalizacija battery managera"""
        # Indeksi baterija:
        # 0 - Senzor betona
        # 1 - Senzor vazduha 
        # 2 - Pumpa
        # 3 - Grijač
        self.battery_count = 4
        self.reset()
    
    def reset(self):
        """Reset svih baterija na početno stanje"""
        # Nivoi baterija (0-100%)
        self.battery_levels = [100.0] * self.battery_count
        
        # Status baterija (da li su "žive")
        self.battery_alive = [True] * self.battery_count
        
        # Potrošnja po satu u normalnim uslovima (%)
        self.normal_drain_rate = 0.5  # 0.5% na sat = 1% na 2h
        
        # Potrošnja po satu za loše baterije (%)
        self.bad_drain_rate = 4.0  # 4% na sat
        
        # Dodatna potrošnja za aktuatore kada rade
        self.actuator_active_drain = 2.0  # 2% dodatno na sat kada radi
    
    def update(self, step_minutes: int, bad_batteries: List[int] = None, 
               active_actuators: List[int] = None):
        """
        Ažuriranje stanja baterija
        
        Args:
            step_minutes (int): Broj minuta koji je prošao
            bad_batteries (List[int]): Lista indeksa loših baterija
            active_actuators (List[int]): Lista indeksa aktivnih aktuatora (2,3)
        """
        if bad_batteries is None:
            bad_batteries = []
        if active_actuators is None:
            active_actuators = []
        
        step_hours = step_minutes / 60.0
        
        for i in range(self.battery_count):
            if not self.battery_alive[i]:
                continue  # Mrtva baterija ostaje na 0%
            
            # Osnovna potrošnja
            if i in bad_batteries:
                drain_rate = self.bad_drain_rate
            else:
                drain_rate = self.normal_drain_rate
            
            # Dodatna potrošnja za aktuatore
            if i >= 2 and i in active_actuators:  # Aktuatori su indeksi 2 i 3
                drain_rate += self.actuator_active_drain
            
            # Računanje potrošnje
            drain_amount = drain_rate * step_hours
            
            # Ažuriranje nivoa baterije
            self.battery_levels[i] = max(0.0, self.battery_levels[i] - drain_amount)
            
            # Ako baterija padne na 0%, označiti kao mrtvu
            if self.battery_levels[i] <= 0:
                self.battery_alive[i] = False
    
    def kill_battery(self, battery_index: int):
        """
        Trenutno ubijanje baterije (postavljanje na 0%)
        
        Args:
            battery_index (int): Indeks baterije (0-3)
        """
        if 0 <= battery_index < self.battery_count:
            self.battery_levels[battery_index] = 0.0
            self.battery_alive[battery_index] = False
    
    def get_battery_level(self, battery_index: int) -> float:
        """
        Dobijanje nivoa baterije
        
        Args:
            battery_index (int): Indeks baterije (0-3)
            
        Returns:
            float: Nivo baterije (0-100%)
        """
        if 0 <= battery_index < self.battery_count:
            return self.battery_levels[battery_index]
        return 0.0
    
    def is_battery_alive(self, battery_index: int) -> bool:
        """
        Provera da li je baterija živa
        
        Args:
            battery_index (int): Indeks baterije (0-3)
            
        Returns:
            bool: True ako je baterija živa
        """
        if 0 <= battery_index < self.battery_count:
            return self.battery_alive[battery_index]
        return False
    
    def get_all_levels(self) -> List[float]:
        """
        Dobijanje svih nivoa baterija
        
        Returns:
            List[float]: Lista nivoa svih baterija
        """
        return self.battery_levels.copy()
    
    def get_battery_status(self, battery_index: int) -> Dict[str, any]:
        """
        Dobijanje detaljnog statusa baterije
        
        Args:
            battery_index (int): Indeks baterije (0-3)
            
        Returns:
            Dict[str, any]: Status baterije
        """
        if 0 <= battery_index < self.battery_count:
            return {
                'level': self.battery_levels[battery_index],
                'alive': self.battery_alive[battery_index],
                'status': self._get_battery_status_text(battery_index)
            }
        return {'level': 0.0, 'alive': False, 'status': 'Invalid'}
    
    def _get_battery_status_text(self, battery_index: int) -> str:
        """
        Dobijanje tekstualnog opisa statusa baterije
        
        Args:
            battery_index (int): Indeks baterije
            
        Returns:
            str: Tekstualni opis statusa
        """
        level = self.battery_levels[battery_index]
        alive = self.battery_alive[battery_index]
        
        if not alive:
            return "Mrtva"
        elif level > 75:
            return "Odličo"
        elif level > 50:
            return "Dobro"
        elif level > 25:
            return "Slabo"
        elif level > 10:
            return "Kritično"
        else:
            return "Vrlo nisko"
    
    def get_sensor_functionality(self, sensor_index: int) -> float:
        """
        Dobijanje funkcionalnosti senzora na osnovu baterije
        Senzori rade slabije kada im je baterija niska
        
        Args:
            sensor_index (int): Indeks senzora (0 ili 1)
            
        Returns:
            float: Funkcionalnost (0.0 - 1.0)
        """
        if sensor_index not in [0, 1]:
            return 0.0
        
        level = self.get_battery_level(sensor_index)
        alive = self.is_battery_alive(sensor_index)
        
        if not alive:
            return 0.0
        elif level > 20:
            return 1.0  # Puna funkcionalnost
        elif level > 10:
            return 0.8  # Smanjena funkcionalnost
        elif level > 5:
            return 0.5  # Značajno smanjena funkcionalnost
        else:
            return 0.2  # Minimalna funkcionalnost
    
    def get_actuator_functionality(self, actuator_index: int) -> float:
        """
        Dobijanje funkcionalnosti aktuatora na osnovu baterije
        Aktuatori rade slabije ili uopšte ne rade kada im je baterija niska
        
        Args:
            actuator_index (int): Indeks aktuatora (2 ili 3)
            
        Returns:
            float: Funkcionalnost (0.0 - 1.0)
        """
        if actuator_index not in [2, 3]:
            return 0.0
        
        level = self.get_battery_level(actuator_index)
        alive = self.is_battery_alive(actuator_index)
        
        if not alive:
            return 0.0
        elif level > 15:
            return 1.0  # Puna funkcionalnost
        elif level > 10:
            return 0.7  # Smanjena funkcionalnost
        elif level > 5:
            return 0.4  # Značajno smanjena funkcionalnost
        else:
            return 0.0  # Ne radi
    
    def get_summary(self) -> Dict[str, any]:
        """
        Dobijanje kompletnog sažetka stanja svih baterija
        
        Returns:
            Dict[str, any]: Sažetak stanja baterija
        """
        battery_names = ["Senzor Beton", "Senzor Vazduh", "Pumpa", "Grijač"]
        
        summary = {
            'batteries': [],
            'total_alive': sum(self.battery_alive),
            'average_level': sum(self.battery_levels) / self.battery_count,
            'critical_batteries': []
        }
        
        for i in range(self.battery_count):
            battery_info = {
                'index': i,
                'name': battery_names[i],
                'level': self.battery_levels[i],
                'alive': self.battery_alive[i],
                'status': self._get_battery_status_text(i)
            }
            summary['batteries'].append(battery_info)
            
            # Dodavanje kritičnih baterija
            if self.battery_levels[i] < 20 and self.battery_alive[i]:
                summary['critical_batteries'].append(battery_info)
        
        return summary