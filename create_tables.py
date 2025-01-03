from app.common.config import Config  # Подгружаем конфигурацию
from app.common.database import Base, engine
from app.daily_review.models import DailyReviewState, DailyReviewQuestions, DailyReviewAnswers

# Проверка, что DATABASE_URL загружен из Config
if not Config.DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в конфигурации.")

def create_tables():
    """Создание таблиц в базе данных."""
    Base.metadata.create_all(engine)
    print("Таблицы успешно созданы!")

if __name__ == "__main__":
    create_tables()
