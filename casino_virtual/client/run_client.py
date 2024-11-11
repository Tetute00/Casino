import tkinter as tk
from tkinter import ttk, messagebox
import socketio
import json
import requests
from datetime import datetime

class CasinoClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Casino - Horse Racing")
        self.root.geometry("1200x800")  # Adjusted to make space for chats
        
        self.sio = socketio.Client()
        self.setup_socket_events()
        
        self.current_user = None
        self.current_room = None
        self.rooms_list = None
        
        # Crear frames principales
        self.auth_frame = ttk.Frame(self.root)
        self.game_frame = ttk.Frame(self.root)
        
        self.setup_auth_ui()
        self.setup_game_ui()
        
        # Mostrar frame de autenticación inicialmente
        self.show_auth_frame()

    def setup_socket_events(self):
        @self.sio.on('connect')
        def on_connect():
            print("Connected to server")
            self.fetch_rooms()
            self.sio.emit('join_global_chat')

        @self.sio.on('user_joined')
        def on_user_joined(data):
            self.update_players_list(data['players'])
            self.add_chat_message(f"System: {data['username']} joined the room", room_chat=True)

        @self.sio.on('user_left')
        def on_user_left(data):
            self.add_chat_message(f"System: {data['username']} left the room", room_chat=True)

        @self.sio.on('chat_message')
        def on_chat_message(data):
            self.add_chat_message(f"{data['username']}: {data['message']}", room_chat=True)

        @self.sio.on('global_chat_message')
        def on_global_chat_message(data):
            self.add_chat_message(f"{data['username']}: {data['message']}", room_chat=False)

        @self.sio.on('bet_placed')
        def on_bet_placed(data):
            self.add_chat_message(f"System: Bet placed - ${data['amount']}", room_chat=True)

        @self.sio.on('room_joined')
        def on_room_joined(data):
            self.current_room = data['room_id']
            self.update_players_list(data['players'])
            if 'game_type' in data:
                self.prepare_game_interface(data['game_type'])
            else:
                messagebox.showerror("Error", "Game type not found")
            
            self.update_players_list(data.get('players', []))
            self.prepare_game_interface(data['game_type'])

        @self.sio.on('room_left')
        def on_room_left(data):
            username = data['username']
            messagebox.showinfo("Sala", f"{username} ha dejado la sala")
    
    def send_room_message(self):
        if not self.current_room:
            messagebox.showwarning("Warning", "Please join a room first")
            return

        message = self.room_chat_entry.get()
        if message.strip():
            self.sio.emit('chat_message', {
                'room_id': self.current_room,
                'username': self.current_user['username'],
                'message': message
            })
            self.room_chat_entry.delete(0, tk.END)

    def setup_auth_ui(self):
        # Login Frame
        login_frame = ttk.LabelFrame(self.auth_frame, text="Login")
        login_frame.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(login_frame, text="Username:").pack(padx=5, pady=2)
        self.login_username = ttk.Entry(login_frame)
        self.login_username.pack(padx=5, pady=2)
        
        ttk.Label(login_frame, text="Password:").pack(padx=5, pady=2)
        self.login_password = ttk.Entry(login_frame, show="*")
        self.login_password.pack(padx=5, pady=2)
        
        ttk.Button(login_frame, text="Login", command=self.handle_login).pack(pady=5)
        
        # Register Frame
        register_frame = ttk.LabelFrame(self.auth_frame, text="Register")
        register_frame.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(register_frame, text="Username:").pack(padx=5, pady=2)
        self.register_username = ttk.Entry(register_frame)
        self.register_username.pack(padx=5, pady=2)
        
        ttk.Label(register_frame, text="Password:").pack(padx=5, pady=2)
        self.register_password = ttk.Entry(register_frame, show="*")
        self.register_password.pack(padx=5, pady=2)
        
        ttk.Button(register_frame, text="Register", command=self.handle_register).pack(pady=5)

    def setup_game_ui(self):
        # Header
        self.header_frame = ttk.Frame(self.game_frame)
        self.header_frame.pack(fill="x", padx=10, pady=5)
        
        self.user_label = ttk.Label(self.header_frame, text="")
        self.user_label.pack(side="left")
        
        self.balance_label = ttk.Label(self.header_frame, text="")
        self.balance_label.pack(side="left", padx=20)
        
        self.level_label = ttk.Label(self.header_frame, text="")
        self.level_label.pack(side="left", padx=20)
        
        self.xp_progress = ttk.Progressbar(self.header_frame, length=200, mode='determinate')
        self.xp_progress.pack(side="left", padx=20)
        
        ttk.Button(self.header_frame, text="Logout", command=self.handle_logout).pack(side="right")
        
        # Main Menu with game options
        self.main_menu_frame = ttk.Frame(self.game_frame)
        self.main_menu_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ttk.Button(self.main_menu_frame, text="Multiplayer Games", command=self.show_multiplayer_games).pack(pady=10)
        ttk.Button(self.main_menu_frame, text="Solo Games", command=self.show_solo_games).pack(pady=10)
        ttk.Button(self.main_menu_frame, text="Store", command=self.show_store).pack(pady=10)
        ttk.Button(self.main_menu_frame, text="Inventory", command=self.show_inventory).pack(pady=10)
        ttk.Button(self.main_menu_frame, text="Rewards", command=self.show_rewards).pack(pady=10)
        ttk.Button(self.main_menu_frame, text="Missions", command=self.show_missions).pack(pady=10)
        
        # Game Content
        self.content_frame = ttk.Frame(self.game_frame)
        
        # Chat Frames
        chat_frame = ttk.Frame(self.root)
        chat_frame.place(relx=0.8, rely=0, relwidth=0.2, relheight=1)
        
        # Global Chat
        global_chat_frame = ttk.LabelFrame(chat_frame, text="Global Chat")
        global_chat_frame.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        
        self.global_chat_text = tk.Text(global_chat_frame, height=15)
        self.global_chat_text.pack(fill="both", expand=True, pady=5)
        
        global_chat_input_frame = ttk.Frame(global_chat_frame)
        global_chat_input_frame.pack(fill="x")
        
        self.global_chat_entry = ttk.Entry(global_chat_input_frame)
        self.global_chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(global_chat_input_frame, text="Send", command=self.send_global_message).pack(side="right")
        
        # Room Chat
        room_chat_frame = ttk.LabelFrame(chat_frame, text="Room Chat")
        room_chat_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        self.room_chat_text = tk.Text(room_chat_frame, height=15)
        self.room_chat_text.pack(fill="both", expand=True, pady=5)
        
        room_chat_input_frame = ttk.Frame(room_chat_frame)
        room_chat_input_frame.pack(fill="x")
        
        self.room_chat_entry = ttk.Entry(room_chat_input_frame)
        self.room_chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(room_chat_input_frame, text="Send", command=self.send_room_message).pack(side="right")

    def show_auth_frame(self):
        self.game_frame.pack_forget()
        self.auth_frame.pack(fill="both", expand=True)

    def show_game_frame(self):
        self.auth_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.main_menu_frame.pack(fill="both", expand=True)

    def handle_login(self):
        username = self.login_username.get()
        password = self.login_password.get()
        
        try:
            response = requests.post('http://4.233.146.61:5000/api/login', 
                                  json={'username': username, 'password': password})
            
            if response.ok:
                data = response.json()
                self.current_user = {
                    'id': data['user_id'],
                    'username': data['username'],
                    'balance': data['balance'],
                    'level': data['level'],
                    'xp': data['xp']
                }
                self.sio.connect('http://4.233.146.61:5000')
                self.show_game_frame()
                self.update_user_info()
            else:
                messagebox.showerror("Error", response.json()['error'])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_register(self):
        username = self.register_username.get()
        password = self.register_password.get()
        
        try:
            response = requests.post('http://4.233.146.61:5000/api/register', 
                                  json={'username': username, 'password': password})
            
            if response.ok:
                messagebox.showinfo("Success", "Registration successful! Please login.")
                self.register_username.delete(0, tk.END)
                self.register_password.delete(0, tk.END)
            else:
                messagebox.showerror("Error", response.json()['error'])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_logout(self):
        if self.sio.connected:
            self.sio.disconnect()
        self.current_user = None
        self.current_room = None
        self.show_auth_frame()

    def update_user_info(self):
        if self.current_user:
            self.user_label['text'] = f"User: {self.current_user['username']}"
            self.balance_label['text'] = f"Balance: ${self.current_user['balance']}"
            self.level_label['text'] = f"Level: {self.current_user['level']}"
            self.xp_progress['value'] = self.current_user['xp']
            self.xp_progress['maximum'] = 100

    def show_multiplayer_games(self):
        self.main_menu_frame.pack_forget()
        self.content_frame.pack(fill="both", expand=True)
        # Display multiplayer games options

    def show_solo_games(self):
        self.main_menu_frame.pack_forget()
        self.content_frame.pack(fill="both", expand=True)
        # Display solo games options

    def show_store(self):
        self.main_menu_frame.pack_forget()
        self.content_frame.pack(fill="both", expand=True)
        # Display store options

    def show_inventory(self):
        self.main_menu_frame.pack_forget()
        self.content_frame.pack(fill="both", expand=True)
        # Display inventory options

    def show_rewards(self):
        self.main_menu_frame.pack_forget()
        self.content_frame.pack(fill="both", expand=True)
        # Display rewards

    def show_missions(self):
        self.main_menu_frame.pack_forget()
        self.content_frame.pack(fill="both", expand=True)
        # Display missions

    def create_room(self):
        create_room_window = tk.Toplevel(self.root)
        create_room_window.title("Crear Sala")
        create_room_window.geometry("300x250")

        ttk.Label(create_room_window, text="Nombre de la Sala:").pack(pady=(10,5))
        room_name_entry = ttk.Entry(create_room_window, width=30)
        room_name_entry.pack(pady=5)

        ttk.Label(create_room_window, text="Tipo de Juego:").pack(pady=(10,5))
        game_types = ["Carreras de Caballos", "Blackjack", "Ruleta"]
        game_type_combo = ttk.Combobox(create_room_window, values=game_types, state="readonly")
        game_type_combo.pack(pady=5)

        ttk.Label(create_room_window, text="Máximo de Jugadores:").pack(pady=(10,5))
        max_players_entry = ttk.Entry(create_room_window, width=10)
        max_players_entry.pack(pady=5)

        ttk.Label(create_room_window, text="Apuesta Mínima:").pack(pady=(10,5))
        min_bet_entry = ttk.Entry(create_room_window, width=10)
        min_bet_entry.pack(pady=5)

        def submit_room():
            name = room_name_entry.get()
            game_type = game_type_combo.get()
            max_players = max_players_entry.get()
            min_bet = min_bet_entry.get()

            if not name or not game_type or not max_players or not min_bet:
                messagebox.showwarning("Advertencia", "Por favor, complete todos los campos")
                return

            try:
                response = requests.post('http://4.233.146.61:5000/api/rooms/create', 
                                         json={
                                             'name': name, 
                                             'game_type': game_type.lower().replace(' ', '_'), 
                                             'created_by': self.current_user['username'],
                                             'max_players': int(max_players),
                                             'min_bet': float(min_bet)
                                         })
                
                if response.ok:
                    room_data = response.json()
                    messagebox.showinfo("Éxito", f"Sala {name} creada con ID: {room_data['room_id']}")
                    create_room_window.destroy()
                    self.fetch_rooms()
                    
                    self.current_room = room_data['room_id']
                    self.sio.emit('join_room', {
                        'room_id': room_data['room_id'],
                        'username': self.current_user['username']
                    })
                else:
                    messagebox.showerror("Error", response.json().get('error', 'Error desconocido'))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(create_room_window, text="Crear Sala", command=submit_room).pack(pady=10)

    def join_selected_room(self):
        selection = self.rooms_list.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Por favor, seleccione una sala")
            return
        
        room_id = selection[0]
        
        try:
            self.sio.emit('join_room', {
                'room_id': room_id,
                'username': self.current_user['username']
            })
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def prepare_game_interface(self, game_type):
        if game_type == 'horse_race':
            self.horse_select['values'] = ["Rayo", "Tormenta", "Veloz", "Relámpago"]
            self.sio.emit('create_race', {'room_id': self.current_room})

    def update_players_list(self, players):
        print("Jugadores en la sala:", players)

    def update_rooms_list(self, rooms):
        for i in self.rooms_list.get_children():
            self.rooms_list.delete(i)
        for room_id, room in rooms.items():
            self.rooms_list.insert('', 'end', iid=room_id, values=(room['name'], len(room['players'])))

    def fetch_rooms(self):
        try:
            response = requests.get('http://4.233.146.61:5000/api/rooms')
            if response.ok:
                rooms = response.json()
                self.update_rooms_list(rooms)
            else:
                messagebox.showerror("Error", "Failed to fetch rooms")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def place_bet(self):
        if not self.current_room:
            messagebox.showwarning("Warning", "Please join a room first")
            return
            
        horse = self.horse_select.get()
        amount = self.bet_amount.get()
        
        try:
            amount = float(amount)
            self.sio.emit('place_bet', {
                'user_id': self.current_user['id'],
                'room_id': self.current_room,
                'amount': amount,
                'bet_type': 'horse',
                'horse_id': horse
            })
        except ValueError:
            messagebox.showerror("Error", "Invalid bet amount")

    def send_message(self):
        if not self.current_room:
            messagebox.showwarning("Warning", "Please join a room first")
            return
            
        message = self.room_chat_entry.get()
        if message.strip():
            self.sio.emit('chat_message', {
                'room_id': self.current_room,
                'username': self.current_user['username'],
                'message': message
            })
            self.room_chat_entry.delete(0, tk.END)

    def send_global_message(self):
        message = self.global_chat_entry.get()
        if message.strip():
            self.sio.emit('global_chat_message', {
                'username': self.current_user['username'],
                'message': message
            })
            self.global_chat_entry.delete(0, tk.END)

    def add_chat_message(self, message, room_chat=True):
        if room_chat:
            self.room_chat_text.insert(tk.END, f"{message}\n")
            self.room_chat_text.see(tk.END)
        else:
            self.global_chat_text.insert(tk.END, f"{message}\n")
            self.global_chat_text.see(tk.END)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = CasinoClient()
    client.run()