from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.common.database import Base

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    public_id = Column(String, nullable=False)
    caption = Column(String(100), nullable=False)

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    text = Column(String(250), nullable=False)
    is_completed = Column(Boolean, default=False)
    position = Column(Integer, nullable=False)
