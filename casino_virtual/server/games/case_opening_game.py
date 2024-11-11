from base_game import BaseGame
import random

class CaseOpeningGame(BaseGame):
    def __init__(self):
        super().__init__()
        self.items = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]

    def open_case(self, player):
        if not self.is_active:
            item = random.choice(self.items)
            return player.add_item_to_inventory(item)

    def start_game(self):
        self.is_active = True

    def end_game(self):
        self.is_active = False