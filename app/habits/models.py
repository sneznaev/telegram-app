from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.common.database import Base
from datetime import datetime


class Habit(Base):
    __tablename__ = 'habits'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)  # ID пользователя из Telegram
    name = Column(String(100), nullable=False)  # Название привычки
    type = Column(String(20), nullable=False)  # 'yes_no' или 'measurable'
    target_value = Column(Float, nullable=True)  # Цель для измеримых привычек
    period = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    color = Column(String(7), nullable=False, default="#FFFFFF")  # Цвет привычки (по умолчанию белый)
    created_at = Column(DateTime, default=datetime.utcnow)  # Дата создания


class HabitLog(Base):
    __tablename__ = 'habit_logs'
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=False)  # Привязка к привычке
    date = Column(Date, nullable=False)  # Дата выполнения
    value = Column(Float, nullable=True)  # Значение выполнения (для измеримых привычек)
    is_completed = Column(Boolean, nullable=False, default=False)  # Выполнена ли цель

    habit = relationship('Habit', backref='logs')  # Связь с привычкой

    def __init__(self, habit, date, value=None):
        self.habit_id = habit.id
        self.date = date
        self.value = value

        # Автоматическая проверка выполнения цели
        if habit.type == "yes_no":
            self.is_completed = value is not None  # Для да/нет: просто наличие значения
        elif habit.type == "measurable":
            self.is_completed = value is not None and value >= habit.target_value  # Для измеримых: >= target_value
