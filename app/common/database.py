from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set in environment variables.")
    raise ValueError("DATABASE_URL is not set in environment variables.")

try:
    # Создаем подключение к базе данных
    engine = create_engine(DATABASE_URL)
    Base = declarative_base()
    session_factory = sessionmaker(bind=engine)
    db_session = scoped_session(session_factory)
except Exception as e:
    logger.error(f"Ошибка подключения к базе данных: {e}")
    raise

def init_db():
    """
    Функция для инициализации базы данных: создает все таблицы на основе моделей.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("База данных успешно инициализирована.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise
