# app/daily_review/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from app.common.database import Base

class DailyReviewState(Base):
    __tablename__ = "daily_review_states"
    id = Column(Integer, primary_key=True)  # Уникальный идентификатор отчета
    user_id = Column(Integer, nullable=False)  # Связь с пользователем
    date = Column(Date, nullable=False)  # Дата отчета
    energy_level = Column(Integer, nullable=False)  # Оценка энергии
    happiness_level = Column(Integer, nullable=False)  # Оценка счастья
    stress_level = Column(Integer, nullable=False)  # Оценка стресса

    # Связь с ответами
    answers = relationship("DailyReviewAnswers", backref="report", cascade="all, delete-orphan")

class DailyReviewQuestions(Base):
    __tablename__ = 'daily_review_questions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    question_text = Column(String, nullable=False)

class DailyReviewAnswers(Base):
    __tablename__ = "daily_review_answers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    question_id = Column(Integer, ForeignKey("daily_review_questions.id"), nullable=False)
    answer = Column(Text, nullable=False)
    report_id = Column(Integer, ForeignKey("daily_review_states.id"), nullable=False)
