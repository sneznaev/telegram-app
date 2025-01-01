from flask import render_template, session, jsonify, redirect, url_for, request
from app.common.logger import logger
from app.common.config import Config
from app.common.database import db_session
from telegram.ext import Application
import asyncio

from . import main_bp

# Telegram Application
loop = asyncio.new_event_loop()
application = None

def initialize_telegram_application():
    """Инициализируем Telegram Application."""
    global application
    application = Application.builder().token(Config.TG_BOT_TOKEN).build()
    loop.run_until_complete(application.initialize())
    logger.info("Telegram Application инициализировано.")

@main_bp.route("/")
def index():
    """
    Главная страница приложения.
    """
    user_id = session.get("user_id")
    if user_id:
        logger.info(f"Пользователь {user_id} вошел на главную страницу.")
    else:
        logger.warning("Неавторизованный пользователь попытался открыть главную страницу.")
    return render_template("index.html", tg_app_url=Config.TG_APP_URL)

@main_bp.route("/login")
def login():
    """
    Фиктивная авторизация для локального тестирования.
    """
    session['user_id'] = 1
    session['first_name'] = "Тестовый пользователь"
    logger.info("Тестовый пользователь авторизован.")
    return redirect(url_for('main.index'))

@main_bp.route("/logout")
def logout():
    """
    Выход из системы.
    """
    user_id = session.pop('user_id', None)
    if user_id:
        logger.info(f"Пользователь {user_id} вышел из системы.")
    else:
        logger.warning("Попытка выхода неавторизованного пользователя.")
    return redirect(url_for('main.index'))

@main_bp.route("/session-user", methods=["GET"])
def session_user():
    """
    Возвращает информацию о текущем пользователе из сессии.
    """
    user_id = session.get("user_id")
    first_name = session.get("first_name", "Гость")
    logger.info(f"Получена информация о пользователе: user_id={user_id}, first_name={first_name}.")
    return jsonify({"user_id": user_id, "first_name": first_name})

@main_bp.route("/webhook/<token>", methods=["POST"])
def webhook(token):
    """
    Обработка обновлений Telegram.
    """
    if token != Config.TG_BOT_TOKEN:
        return jsonify({"error": "Invalid token"}), 403

    update = request.get_json()
    if application and update:
        user_data = update.get("message", {}).get("from", {})
        if user_data:
            session['user_id'] = user_data.get('id')  # Сохраняем ID пользователя в сессии
            logger.info(f"ID пользователя {user_data.get('id')} сохранен в сессии.")
        asyncio.run(application.process_update(update))
        return jsonify({"status": "ok"}), 200

    return jsonify({"error": "Failed to process update"}), 400

@main_bp.route("/user", methods=["POST"])
def get_user_info():
    """
    Маршрут для получения данных о пользователе.
    """
    user_data = request.json
    if user_data:
        user_name = user_data.get("first_name", "Гость")
        user_id = user_data.get("id", "Неизвестен")
        session['user_id'] = user_id  # Сохраняем ID пользователя в сессии

        logger.info(f"Сессия обновлена для пользователя {user_name} с ID {user_id}.")
        return jsonify({"message": f"{user_name}"})
    return jsonify({"error": "Данные пользователя не переданы"}), 400

# Инициализация Telegram Application при старте
try:
    initialize_telegram_application()
except Exception as e:
    logger.error(f"Ошибка инициализации Telegram Application: {e}")
