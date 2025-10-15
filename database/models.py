"""
SQLAlchemy модели для базы данных.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Модель пользователя Telegram."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Project(Base):
    """Модель проекта (заказчика)."""
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="projects")
    uploads = relationship("Upload", back_populates="project", cascade="all, delete-orphan")
    beer_items = relationship("BeerItem", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(name={self.name}, user_id={self.user_id})>"


class Upload(Base):
    """Модель загруженного файла."""
    
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="uploads")
    
    def __repr__(self):
        return f"<Upload(filename={self.filename}, project_id={self.project_id})>"


class BeerItem(Base):
    """Модель позиции пива."""
    
    __tablename__ = "beer_items"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    brewery = Column(String(255), nullable=True)
    name = Column(String(500), nullable=True)
    style = Column(String(255), nullable=True)
    volume = Column(String(100), nullable=True)
    price = Column(String(100), nullable=True)
    raw_data = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="beer_items")
    
    def __repr__(self):
        return f"<BeerItem(name={self.name}, brewery={self.brewery})>"


class Order(Base):
    """Модель заказа."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # Nullable для быстрых заказов
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="draft")  # draft, confirmed, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Поля для быстрого заказа
    filename = Column(String(255), nullable=True)  # Имя загруженного файла
    original_data = Column(Text, nullable=True)  # JSON исходных данных
    order_data = Column(Text, nullable=True)  # JSON данных заказа
    
    project = relationship("Project")
    user = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, project_id={self.project_id}, status={self.status})>"


class OrderItem(Base):
    """Модель позиции в заказе."""
    
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    beer_item_id = Column(Integer, ForeignKey("beer_items.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="items")
    beer_item = relationship("BeerItem")
    
    def __repr__(self):
        return f"<OrderItem(order_id={self.order_id}, quantity={self.quantity})>"

