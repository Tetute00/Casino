from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from .models import Base, User, UserRole, Horse, Room, Bet, Transaction
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os

class DatabaseHandler:
    def __init__(self, db_url=None):
        if db_url is None:
            # Crear la carpeta data si no existe
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            # Crear la ruta completa para la base de datos
            db_path = os.path.join(data_dir, 'casino.db')
            db_url = f'sqlite:///{db_path}'
        
        self.engine = create_engine(db_url)
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.SessionFactory)
        
    def init_db(self):
        """Inicializa la base de datos creando todas las tablas"""
        try:
            Base.metadata.create_all(self.engine)
            return True
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            return False

    def get_session(self):
        """Obtiene una sesión de base de datos"""
        return self.Session()

    def close_session(self):
        """Cierra la sesión actual"""
        self.Session.remove()

    def create_user(self, username, password, role=UserRole.PLAYER):
        session = self.get_session()
        try:
            password_hash = generate_password_hash(password)  # Hash de la contraseña
            new_user = User(
                username=username,
                password=password_hash,
                role=UserRole.PLAYER,  # Usar el enum directamente
                balance=1000.0,  # Balance inicial
                level=1,  # Inicializar level
                xp=0  # Inicializar xp
            )
            session.add(new_user)
            session.commit()
            return new_user
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error creating user: {e}")
            return None
        finally:
            session.close()

    def get_user(self, username):
        """Obtiene un usuario por su nombre de usuario"""
        session = self.get_session()
        try:
            return session.query(User).filter_by(username=username).first()
        finally:
            session.close()

    def verify_password(self, stored_password_hash, provided_password):
        """Verifica si la contraseña proporcionada coincide con el hash almacenado"""
        try:
            return check_password_hash(stored_password_hash, provided_password)
        except Exception as e:
            logging.error(f"Error verifying password: {e}")
            return False

    def create_room(self, name, game_type, max_players, min_bet, created_by):
        """Crea una nueva sala de juego"""
        session = self.get_session()
        try:
            new_room = Room(
                name=name,
                game_type=game_type,
                max_players=max_players,
                min_bet=min_bet,
                created_by=created_by
            )
            session.add(new_room)
            session.commit()
            return new_room
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error creating room: {e}")
            return None
        finally:
            session.close()

    def get_active_rooms(self):
        """Obtiene todas las salas activas"""
        session = self.get_session()
        try:
            return session.query(Room).filter_by(is_active=True).all()
        finally:
            session.close()

    def create_bet(self, user_id, room_id, amount, bet_type):
        """Crea una nueva apuesta"""
        session = self.get_session()
        try:
            new_bet = Bet(
                user_id=user_id,
                room_id=room_id,
                amount=amount,
                bet_type=bet_type
            )
            session.add(new_bet)
            
            # Actualizar el balance del usuario
            user = session.query(User).filter_by(id=user_id).first()
            if user and user.balance >= amount:
                user.balance -= amount
                # Crear transacción
                transaction = Transaction(
                    user_id=user_id,
                    amount=-amount,
                    type='bet'
                )
                session.add(transaction)
                session.commit()
                return new_bet
            else:
                session.rollback()
                return None
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error creating bet: {e}")
            return None
        finally:
            session.close()

    def create_horse(self, name):
        """Crea un nuevo caballo"""
        session = self.get_session()
        try:
            new_horse = Horse(name=name)
            session.add(new_horse)
            session.commit()
            return new_horse
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error creating horse: {e}")
            return None
        finally:
            session.close()

    def update_horse_stats(self, horse_id, won=False):
        """Actualiza las estadísticas de un caballo"""
        session = self.get_session()
        try:
            horse = session.query(Horse).filter_by(id=horse_id).first()
            if horse:
                horse.races += 1
                if won:
                    horse.wins += 1
                horse.win_rate = horse.wins / horse.races
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error updating horse stats: {e}")
            return False
        finally:
            session.close()
    def add_item_to_inventory(self, user_id, item_name):
        session = self.get_session()
        try:
            new_item = InventoryItem(user_id=user_id, item_name=item_name)
            session.add(new_item)
            session.commit()
            return new_item
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error adding item to inventory: {e}")
            return None
        finally:
            session.close()

    def get_inventory(self, user_id):
        session = self.get_session()
        try:
            return session.query(InventoryItem).filter_by(user_id=user_id).all()
        finally:
            session.close()

# Crear una instancia global del manejador de base de datos
db = DatabaseHandler()