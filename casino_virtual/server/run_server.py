from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room
from database.db_handler import db
from database.models import UserRole
import logging
import os
import random
import time
import requests
from threading import Thread

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Flask y SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key_123')
socketio = SocketIO(app, cors_allowed_origins="*")

# Sistema de carreras
class Horse:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.position = 0
        self.speed_base = random.uniform(0.8, 1.2)
        self.finished = False

class HorseRace:
    def __init__(self, track_length: int = 100):
        self.track_length = track_length
        self.horses = []
        self.is_active = False
        self.winner = None
        self.positions = {}
        
    def add_horse(self, horse_id: int, horse_name: str):
        horse = Horse(horse_id, horse_name)
        self.horses.append(horse)
        
    def start_race(self):
        if len(self.horses) < 2:
            return False, "Se necesitan al menos 2 caballos para iniciar la carrera"
        self.is_active = True
        return True, "¡La carrera ha comenzado!"
        
    def update_race(self):
        if not self.is_active:
            return {}

        race_finished = True
        positions = {}
        
        for horse in self.horses:
            if not horse.finished:
                speed = horse.speed_base * random.uniform(0.8, 1.2)
                horse.position += speed
                
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

    def get_race_status(self):
        return {
            'is_active': self.is_active,
            'positions': self.positions,
            'winner': self.winner.name if self.winner else None
        }

# Almacenamiento en memoria
connected_users = {}
active_games = {}
races = {}

class Room:
    def __init__(self, name, game_type, created_by):
        self.name = name
        self.game_type = game_type
        self.players = []
        self.state = 'waiting'
        self.created_by = created_by
        self.race = None

class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.room_counter = 0

    def create_room(self, name, game_type, created_by):
        self.room_counter += 1
        room_id = str(self.room_counter)
        room = Room(name, game_type, created_by)
        self.rooms[room_id] = room
        return room_id, room

    def get_room(self, room_id):
        return self.rooms.get(room_id)

    def get_all_rooms(self):
        return self.rooms

room_manager = RoomManager()

@app.route('/')
def home():
    return jsonify({"status": "Server is running", "message": "Welcome to Casino Server"})

@app.route('/api/register', methods=['POST'])
def handle_register():
    try:
        data = request.json
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing username or password'}), 400

        existing_user = db.get_user(data['username'])
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409

        new_user = db.create_user(data['username'], data['password'])

        if new_user:
            return jsonify({'message': 'User created successfully'}), 201
        return jsonify({'error': 'Error creating user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = db.get_user(data['username'])
    
    if user and check_password_hash(user.password, data['password']):
        return jsonify({
            'user_id': user.id,
            'username': user.username,
            'balance': user.balance,
            'role': user.role.value,
            'level':user.level,
            'xp':user.xp,
        }), 200
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    rooms_data = {}
    for room_id, room in room_manager.rooms.items():
        rooms_data[room_id] = {
            'name': room.name,
            'game_type': room.game_type,
            'players': room.players,
            'state': room.state,
            'created_by': room.created_by
        }
    return jsonify(rooms_data)

@app.route('/api/rooms/create', methods=['POST'])
def create_room_endpoint():
    data = request.get_json()
    if not data or 'name' not in data or 'game_type' not in data or 'created_by' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    room_id, room = room_manager.create_room(
        data['name'],
        data['game_type'],
        data['created_by']
    )
    
    return jsonify({
        'room_id': room_id,
        'name': room.name,
        'game_type': room.game_type,
        'state': room.state
    })
@app.route('/api/inventory/<int:user_id>', methods=['GET'])
def get_inventory(user_id):
    items = db.get_inventory(user_id)
    return jsonify([item.item_name for item in items])

@app.route('/api/inventory/add', methods=['POST'])
def add_item_to_inventory():
    data = request.json
    if not data or 'user_id' not in data or 'item_name' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    item = db.add_item_to_inventory(data['user_id'], data['item_name'])
    if item:
        return jsonify({'message': 'Item added successfully'}), 201
    return jsonify({'error': 'Error adding item'}), 500
    
# Socket.IO events
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    user_data = connected_users.get(request.sid)
    if user_data:
        room = user_data.get('room')
        if room:
            leave_room(room)
            emit('user_left', {'username': user_data['username']}, room=room)
        del connected_users[request.sid]
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_room')
def handle_join_room(data):
    room_id = str(data['room_id'])
    username = data['username']
    
    room = room_manager.get_room(room_id)
    if room:
        if username not in room.players:
            room.players.append(username)
        join_room(room_id)
        connected_users[request.sid] = {'username': username, 'room': room_id}
        emit('room_joined', {
            'room_id': room_id,
            'name': room.name,
            'players': room.players,
            'game_type': room.game_type,
            'created_by': room.created_by  # Asegúrate de enviar el creador de la sala
        }, room=room_id)
    else:
        emit('error', {'message': 'Room not found'})

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = str(data['room_id'])
    username = data['username']
    
    room = room_manager.get_room(room_id)
    if room and username in room.players:
        room.players.remove(username)
        leave_room(room_id)
        if request.sid in connected_users:
            del connected_users[request.sid]
        emit('room_left', {'username': username}, room=room_id)

@socketio.on('create_race')
def handle_create_race(data):
    room_id = str(data['room_id'])
    room = room_manager.get_room(room_id)
    
    if room:
        race = HorseRace()
        # Añadir caballos predefinidos
        horses = [
            ("Rayo", 1),
            ("Tormenta", 2),
            ("Veloz", 3),
            ("Relámpago", 4)
        ]
        
        for name, horse_id in horses:
            race.add_horse(horse_id, name)
        
        room.race = race
        emit('race_created', {
            'message': 'Carrera creada',
            'horses': [{'id': h.id, 'name': h.name} for h in race.horses]
        }, room=room_id)
    else:
        emit('error', {'message': 'Room not found'})

@socketio.on('close_room')
def handle_close_room(data):
    room_id = data['room_id']
    room_manager.remove_player_from_room(room_id, connected_users[request.sid]['username'])  # Eliminar al usuario de la sala
    emit('room_closed', {'message': 'La sala ha sido cerrada'}, room=room_id)

@socketio.on('start_race')
def handle_start_race(data):
    room_id = str(data['room_id'])
    room = room_manager.get_room(room_id)
    
    if not room or not room.race:
        emit('error', {'message': 'Race not found'})
        return
    
    success, message = room.race.start_race()
    if success:
        def race_updates():
            race = room.race
            while race.is_active:
                status = race.update_race()
                emit('race_update', status, room=room_id)
                time.sleep(0.5)
            
            emit('race_finished', {
                'winner': race.winner.name,
                'final_positions': race.positions
            }, room=room_id)
            
        socketio.start_background_task(race_updates)
        emit('race_started', {'message': message}, room=room_id)
    else:
        emit('error', {'message': message})

@socketio.on('place_bet')
def handle_bet(data):
    bet = db.create_bet(
        user_id=data['user_id'],
        room_id=data['room_id'],
        amount=data['amount'],
        bet_type=data['bet_type']
    )
    
    if bet:
        emit('bet_placed', {
            'user_id': data['user_id'],
            'amount': data['amount'],
            'bet_type': data['bet_type']
        }, room=str(data['room_id']))
    else:
        emit('bet_error', {
            'message': 'Error placing bet'
        }, room=request.sid)

@socketio.on('chat_message')
def handle_message(data):
    room_id = str(data['room_id'])
    emit('chat_message', {
        'username': data['username'],
        'message': data['message']
    }, room=room_id)

if __name__ == '__main__':
    db.init_db()
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, 
                host='0.0.0.0',
                port=port, 
                debug=True,
                allow_unsafe_werkzeug=True)