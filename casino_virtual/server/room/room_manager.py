"""Room management system"""
class RoomManager:
    def __init__(self):
        self.rooms = {}  # Almacena las salas activas
        self.room_counter = 0

    def create_room(self, name, game_type, created_by):
        """Crea una nueva sala"""
        self.room_counter += 1
        room_id = str(self.room_counter)
        self.rooms[room_id] = {
            'id': room_id,
            'name': name,
            'game_type': game_type,
            'players': [],
            'state': 'waiting',
            'created_by': created_by,
            'race': None  # Aquí almacenaremos la carrera cuando se cree
        }
        return room_id, self.rooms[room_id]

    def get_room(self, room_id):
        """Obtiene una sala específica"""
        return self.rooms.get(room_id)

    def get_all_rooms(self):
        """Obtiene todas las salas"""
        return self.rooms

    def add_player_to_room(self, room_id, player_name):
        """Añade un jugador a una sala"""
        if room_id in self.rooms:
            if player_name not in self.rooms[room_id]['players']:
                self.rooms[room_id]['players'].append(player_name)
            return True
        return False

    def remove_player_from_room(self, room_id, player_name):
        """Elimina un jugador de una sala"""
        if room_id in self.rooms:
            if player_name in self.rooms[room_id]['players']:
                self.rooms[room_id]['players'].remove(player_name)
                # Si no quedan jugadores, eliminar la sala
                if not self.rooms[room_id]['players']:
                    del self.rooms[room_id]
            return True
        return False
    def remove_player_from_room(self, room_id, username):
        room = self.get_room(room_id)
        if room and username in room.players:
            room.players.remove(username)
            if not room.players:  # Si no quedan jugadores, eliminar la sala
                self.remove_room(room_id)