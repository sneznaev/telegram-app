from flask import Flask
from app.common.config import Config
from app.common.logger import logger
from app.common.database import init_db
from app.main import main_bp
from app.gallery import gallery_bp
from app.goals import goals_bp

# Создаем приложение Flask
def create_app():
    """Функция создания приложения Flask."""
    app = Flask(__name__, static_folder="app/static")
    app.config.from_object(Config)

    # Регистрация Blueprints
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(gallery_bp, url_prefix="/gallery")
    app.register_blueprint(goals_bp, url_prefix="/goals")

    # Инициализация базы данных
    with app.app_context():
        init_db()

    return app

app = create_app()
    
if __name__ == "__main__":
    if Config.FLASK_ENV == "development":
        logger.info("Запуск приложения в режиме разработки.")
        app.run(host="127.0.0.1", port=5000, debug=True)
    else:
        logger.info("Запуск приложения в production-режиме.")
        app.run(host="0.0.0.0", port=5000)
