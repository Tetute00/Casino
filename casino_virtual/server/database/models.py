from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PLAYER = "PLAYER"
    
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PLAYER)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    level = Column(Integer, default=1)  # Añadir campo level
    xp = Column(Integer, default=0)  # Añadir campo xp
    
    # Relaciones
    transactions = relationship("Transaction", back_populates="user")
    bets = relationship("Bet", back_populates="user")

class Horse(Base):
    __tablename__ = 'horses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    wins = Column(Integer, default=0)
    races = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    race_results = relationship("RaceResult", back_populates="horse")

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    game_type = Column(String(50), nullable=False)  # 'horse_race', 'blackjack', etc.
    max_players = Column(Integer, nullable=False)
    min_bet = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relaciones
    players = relationship("RoomPlayer", back_populates="room")
    bets = relationship("Bet", back_populates="room")

class RoomPlayer(Base):
    __tablename__ = 'room_players'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    room = relationship("Room", back_populates="players")
    user = relationship("User")

class Bet(Base):
    __tablename__ = 'bets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    amount = Column(Float, nullable=False)
    bet_type = Column(String(50))  # Para diferentes tipos de apuestas
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    won = Column(Boolean)
    
    # Relaciones
    user = relationship("User", back_populates="bets")
    room = relationship("Room", back_populates="bets")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float, nullable=False)
    type = Column(String(50))  # 'deposit', 'withdrawal', 'bet', 'win'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="transactions")

class RaceResult(Base):
    __tablename__ = 'race_results'
    
    id = Column(Integer, primary_key=True)
    horse_id = Column(Integer, ForeignKey('horses.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    position = Column(Integer, nullable=False)
    race_time = Column(Float)  # Tiempo que tardó en completar la carrera
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    horse = relationship("Horse", back_populates="race_results")

class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    item_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User", back_populates="inventory_items")

User.inventory_items = relationship("InventoryItem", back_populates="user")

def init_db(db_url='sqlite:///casino.db'):
    """Inicializa la base de datos"""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)