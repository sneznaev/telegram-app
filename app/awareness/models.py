from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.common.database import Base
from datetime import datetime

class AwarenessLog(Base):
    __tablename__ = 'awareness_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)  # ID пользователя из Telegram
    want = Column(Text, nullable=True)           # Что пользователь хочет
    happening = Column(Text, nullable=True)      # Что происходит
    doing = Column(Text, nullable=True)          # Что пользователь делает
    feeling = Column(Text, nullable=True)        # Что пользователь чувствует
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)  # Время записи

    def __repr__(self):
        return f"<AwarenessLog(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp})>"
