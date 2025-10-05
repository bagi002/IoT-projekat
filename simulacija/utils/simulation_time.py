"""
Simulaciono vreme - upravljanje vremenom u simulaciji
Omogućava napredovanje vremena po koracima
"""

from datetime import datetime, timedelta


class SimulationTime:
    """
    Klasa za upravljanje vremenom u simulaciji
    Omogućava napredovanje vremena po definisanim koracima
    """
    
    def __init__(self, start_time: str = "2025-05-05T12:00:00"):
        """
        Inicijalizacija simulacionog vremena
        
        Args:
            start_time (str): Početno vreme u ISO formatu
        """
        self.current_time = datetime.fromisoformat(start_time)
        self.start_time = self.current_time
    
    def advance_time(self, minutes: int):
        """
        Napredovanje vremena za zadati broj minuta
        
        Args:
            minutes (int): Broj minuta za napredovanje
        """
        self.current_time += timedelta(minutes=minutes)
    
    def set_current_time(self, time_str: str):
        """
        Postavljanje trenutnog vremena
        
        Args:
            time_str (str): Vreme u ISO formatu
        """
        self.current_time = datetime.fromisoformat(time_str)
    
    def get_current_time_json(self) -> dict:
        """
        Dobijanje trenutnog vremena kao JSON objekat sa odvojenim poljima
        
        Returns:
            dict: Objekat sa date i time poljima
        """
        return {
            'date': self.current_time.strftime("%Y-%m-%d"),
            'time': self.current_time.strftime("%H:%M:%S")
        }
    
    def set_current_time_from_json(self, date_str: str, time_str: str):
        """
        Postavljanje trenutnog vremena iz odvojenih polja
        
        Args:
            date_str (str): Datum u formatu YYYY-MM-DD
            time_str (str): Vreme u formatu HH:MM:SS
        """
        datetime_str = f"{date_str}T{time_str}"
        self.current_time = datetime.fromisoformat(datetime_str)
    
    def get_current_time(self) -> str:
        """
        Dobijanje trenutnog vremena kao string
        
        Returns:
            str: Trenutno vreme u ISO formatu
        """
        return self.current_time.isoformat()
    
    def get_current_datetime(self) -> datetime:
        """
        Dobijanje trenutnog vremena kao datetime objekat
        
        Returns:
            datetime: Trenutno vreme
        """
        return self.current_time
    
    def get_hour_of_day(self) -> int:
        """
        Dobijanje trenutnog sata u danu (0-23)
        
        Returns:
            int: Sat u danu
        """
        return self.current_time.hour
    
    def get_day_progress(self) -> float:
        """
        Dobijanje progresa dana kao decimalni broj (0.0 - 1.0)
        0.0 = ponoć, 0.5 = podne, 1.0 = ponoć sledećeg dana
        
        Returns:
            float: Progress dana
        """
        total_minutes = self.current_time.hour * 60 + self.current_time.minute
        return total_minutes / (24 * 60)
    
    def get_elapsed_time(self) -> timedelta:
        """
        Dobijanje vremena koje je prošlo od početka simulacije
        
        Returns:
            timedelta: Vreme koje je prošlo
        """
        return self.current_time - self.start_time
    
    def get_elapsed_days(self) -> float:
        """
        Dobijanje broja dana koji su prošli od početka simulacije
        
        Returns:
            float: Broj dana (sa decimalnim delom)
        """
        elapsed = self.get_elapsed_time()
        return elapsed.total_seconds() / (24 * 3600)
    
    def is_daytime(self) -> bool:
        """
        Provera da li je trenutno dan (6:00 - 18:00)
        
        Returns:
            bool: True ako je dan
        """
        hour = self.get_hour_of_day()
        return 6 <= hour < 18
    
    def is_nighttime(self) -> bool:
        """
        Provera da li je trenutno noć (18:00 - 6:00)
        
        Returns:
            bool: True ako je noć
        """
        return not self.is_daytime()
    
    def get_sun_intensity(self) -> float:
        """
        Dobijanje intenziteta sunca na osnovu vremena dana
        Koristi sinusoidalnu funkciju za realističnu simulaciju
        
        Returns:
            float: Intenzitet sunca (0.0 - 1.0)
        """
        hour = self.get_hour_of_day()
        
        # Sunce je najjače u podne (12h), najslabije u ponoć
        if 6 <= hour <= 18:
            # Dan: sinusoidalna kriva od 6h do 18h
            import math
            angle = (hour - 6) * math.pi / 12  # 0 do π
            return math.sin(angle)
        else:
            # Noć: nema sunca
            return 0.0
    
    def get_temperature_factor(self) -> float:
        """
        Dobijanje faktora temperature na osnovu vremena dana
        Najhladnije je ujutru (6h), najtoplije popodne (14h)
        
        Returns:
            float: Faktor temperature (-1.0 do 1.0)
        """
        hour = self.get_hour_of_day()
        
        import math
        # Minimum u 6h, maksimum u 14h
        angle = (hour - 6) * math.pi / 12
        return math.sin(angle)
    
    def reset(self, start_time: str = "2025-05-05T12:00:00"):
        """
        Reset simulacionog vremena na početno stanje
        
        Args:
            start_time (str): Novo početno vreme u ISO formatu
        """
        self.current_time = datetime.fromisoformat(start_time)
        self.start_time = self.current_time
    
    def __str__(self) -> str:
        """
        String reprezentacija trenutnog vremena
        
        Returns:
            str: Formatirano vreme
        """
        return self.current_time.strftime("%Y-%m-%d %H:%M:%S")