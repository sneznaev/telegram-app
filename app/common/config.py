import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DATABASE_URL = os.getenv("DATABASE_URL")
    TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
    TG_APP_URL = f"https://t.me/{os.getenv('TELEGRAM_BOT_USERNAME')}?start"