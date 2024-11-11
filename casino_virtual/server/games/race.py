import random
import time
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Horse:
    id: int
    name: str
    position: float = 0
    speed_base: float = 0
    finished: bool = False

class HorseRace:
    def __init__(self, track_length: int = 100):
        self.track_length = track_length
        self.horses: List[Horse] = []
        self.is_active = False
        self.winner = None
        self.positions = {}
        
    def add_horse(self, horse_id: int, horse_name: str):
        """Añade un caballo a la carrera"""
        horse = Horse(
            id=horse_id,
            name=horse_name,
            speed_base=random.uniform(0.8, 1.2)  # Velocidad base aleatoria
        )
        self.horses.append(horse)
        
    def start_race(self):
        """Inicia la carrera"""
        if len(self.horses) < 2:
            return False, "Se necesitan al menos 2 caballos para iniciar la carrera"
        
        self.is_active = True
        return True, "¡La carrera ha comenzado!"
        
    def update_race(self) -> Dict:
        """Actualiza las posiciones de los caballos"""
        if not self.is_active:
            return {}

        race_finished = True
        positions = {}
        
        for horse in self.horses:
            if not horse.finished:
                # Calcula el movimiento del caballo
                speed = horse.speed_base * random.uniform(0.8, 1.2)
                horse.position += speed
                
                # Verifica si el caballo terminó
                if horse.position >= self.track_length:
                    horse.position = self.track_length
                    horse.finished = True
                    if not self.winner:
                        self.winner = horse
                else:
                    race_finished = False
                    
            positions[horse.id] = {
                'name': horse.name,
                'position': min(100, int((horse.position / self.track_length) * 100)),
                'finished': horse.finished
            }
            
        self.positions = positions
        
        if race_finished:
            self.is_active = False
            
        return {
            'positions': positions,
            'is_active': self.is_active,
            'winner': self.winner.name if self.winner else None
        }

    def get_race_status(self) -> Dict:
        """Obtiene el estado actual de la carrera"""
        return {
            'is_active': self.is_active,
            'positions': self.positions,
            'winner': self.winner.name if self.winner else None
        }