"""Base class for all casino games"""

class BaseGame:
    def __init__(self):
        self.players = []
        self.is_active = False

    def start_game(self):
        """Start the game"""
        raise NotImplementedError

    def end_game(self):
        """End the game"""
        raise NotImplementedError