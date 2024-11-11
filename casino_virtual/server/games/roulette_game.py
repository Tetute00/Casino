from base_game import BaseGame
import random

class RouletteGame(BaseGame):
    def __init__(self):
        super().__init__()
        self.bets = []

    def place_bet(self, player, bet_type, amount):
        if not self.is_active:
            self.bets.append((player, bet_type, amount))

    def start_game(self):
        self.is_active = True
        winning_number = random.randint(0, 36)
        results = self.resolve_bets(winning_number)
        self.end_game()
        return results

    def resolve_bets(self, winning_number):
        results = []
        for bet in self.bets:
            player, bet_type, amount = bet
            if bet_type == winning_number:  # Simplified winning condition
                results.append((player, amount * 36))  # Payout 36:1
            else:
                results.append((player, -amount))
        return results

    def end_game(self):
        self.is_active = False
        self.bets.clear()