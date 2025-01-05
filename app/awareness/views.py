from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from app.common.database import db_session
from app.common.logger import logger
from app.common.auth import login_required
from app.awareness.models import AwarenessLog
from datetime import datetime
from app.common.config import Config


awareness_bp = Blueprint('awareness', __name__, template_folder='templates', static_folder='static')

# Просмотр записей
@awareness_bp.route('/', methods=['GET'])
@login_required
def list_logs():
    user_id = session.get('user_id')
    logger.info(f"Пользователь {user_id} открыл дневник осознанности.")
    logs = db_session.query(AwarenessLog).filter_by(user_id=user_id).order_by(AwarenessLog.timestamp.desc()).all()
    return render_template('awareness_logs.html', logs=logs)

# Добавление записи
@awareness_bp.route('/new', methods=['GET', 'POST'])
@login_required
def add_log():
    user_id = session.get('user_id')
    if request.method == 'POST':
        data = request.form
        new_log = AwarenessLog(
            user_id=user_id,
            want=data.get('want'),
            happening=data.get('happening'),
            doing=data.get('doing'),
            feeling=data.get('feeling')
        )
        db_session.add(new_log)
        db_session.commit()
        logger.info(f"Пользователь {user_id} добавил новую запись осознанности.")
        flash("Запись успешно добавлена.")
        return redirect(url_for('awareness.list_logs'))
    
    logger.info(f"Пользователь {user_id} открыл форму добавления записи.")
    return render_template('add_awareness_log.html')

# Удаление записи
@awareness_bp.route('/<int:log_id>/delete', methods=['POST'])
@login_required
def delete_log(log_id):
    user_id = session.get('user_id')
    logger.info(f"Пользователь {user_id} пытается удалить запись с ID {log_id}.")
    log = db_session.query(AwarenessLog).filter_by(id=log_id, user_id=user_id).first()
    if not log:
        logger.warning(f"Запись с ID {log_id} не найдена для пользователя {user_id}.")
        flash("Запись не найдена!")
        return redirect(url_for('awareness.list_logs'))
    
    db_session.delete(log)
    db_session.commit()
    logger.info(f"Пользователь {user_id} удалил запись с ID {log_id}.")
    flash("Запись успешно удалена.")
    return redirect(url_for('awareness.list_logs'))

# Редактирование записи
@awareness_bp.route('/<int:log_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_log(log_id):
    user_id = session.get('user_id')
    logger.info(f"Пользователь {user_id} открыл редактирование записи с ID {log_id}.")
    log = db_session.query(AwarenessLog).filter_by(id=log_id, user_id=user_id).first()
    if not log:
        logger.warning(f"Запись с ID {log_id} не найдена для пользователя {user_id}.")
        flash("Запись не найдена!")
        return redirect(url_for('awareness.list_logs'))
    
    if request.method == 'POST':
        data = request.form
        log.want = data.get('want', log.want)
        log.happening = data.get('happening', log.happening)
        log.doing = data.get('doing', log.doing)
        log.feeling = data.get('feeling', log.feeling)
        db_session.commit()
        logger.info(f"Пользователь {user_id} обновил запись с ID {log_id}.")
        flash("Запись успешно обновлена.")
        return redirect(url_for('awareness.list_logs'))
    
    return render_template('edit_awareness_log.html', log=log)

# Напоминания через Telegram
@awareness_bp.route('/reminders/send', methods=['POST'])
def send_reminder():
    from telegram import Bot

    bot = Bot(token=Config.TG_BOT_TOKEN)

    users = db_session.query(User).all()  # Здесь предполагается таблица пользователей User
    for user in users:
        bot.send_message(
            chat_id=user.telegram_id,
            text="Напоминание: заполните дневник осознанности! Нажмите ниже, чтобы добавить запись.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Добавить запись", url="https://ваш_сайт/awareness/new")]
            ])
        )
    logger.info("Напоминания успешно отправлены всем пользователям.")
    return jsonify({"status": "success", "message": "Напоминания отправлены."})
