from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from app.common.database import db_session
from app.common.logger import logger
from app.common.auth import login_required
from app.habits.models import Habit, HabitLog
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from flask import redirect, url_for

habits_bp = Blueprint('habits', __name__, template_folder='templates', static_folder='static')


@habits_bp.route('/', methods=['GET'])
@login_required
def list_habits():
    user_id = session.get("user_id")
    logger.info(f"Пользователь {user_id} открыл главную страницу привычек.")
    
    # Получение всех привычек пользователя
    habits = db_session.query(Habit).filter_by(user_id=user_id).all()
    if not habits:
        logger.info(f"У пользователя {user_id} нет созданных привычек.")
    
    # Генерация календаря: несколько дней до текущего дня
    today = datetime.today().date()
    days_to_show = 7  # Количество отображаемых дней
    start_date = today - timedelta(days=days_to_show - 1)  # Начало диапазона дат
    days = [
        {
            "date": start_date + timedelta(days=i),
            "day_name": (start_date + timedelta(days=i)).strftime('%a'),  # День недели
            "day_number": (start_date + timedelta(days=i)).day,  # Число
            "is_today": (start_date + timedelta(days=i)) == today
        } for i in range(days_to_show)
    ][::-1]

    # Формирование данных привычек и их логов
    habits_data = []
    for habit in habits:
        logs = []
        for day in days:
            log = db_session.query(HabitLog).filter_by(habit_id=habit.id, date=day["date"]).first()
            if not log:
                log = HabitLog(habit, day["date"], value=0)  # Значение по умолчанию 0
                db_session.add(log)
            logs.append({"date": day["date"], "value": log.value, "is_completed": log.is_completed})
        
        habits_data.append({
            "id": habit.id,
            "name": habit.name,
            "type": habit.type,
            "color": habit.color,
            "logs": logs
        })
    
    db_session.commit()  # Сохранение добавленных логов

    # Рендеринг шаблона
    return render_template('habits.html', habits=habits_data, days=days)






@habits_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_habit():
    user_id = session.get('user_id')
    if not user_id:
        logger.error("Неавторизованный пользователь пытается создать привычку.")
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == 'POST':
        # Обработка формы
        data = request.form
        name = data.get('name')
        type_ = data.get('type')
        target_value = data.get('target_value')
        period = data.get('period')
        color = data.get('color', "#FFFFFF")

        # Проверка имени
        if not name or len(name) > 100:
            logger.error(f"Неверное имя привычки: {name}")
            return jsonify({"error": "Invalid habit name"}), 400

        # Проверка типа привычки
        if type_ not in ['yes_no', 'measurable']:
            logger.error(f"Неверный тип привычки: {type_}")
            return jsonify({"error": "Invalid habit type"}), 400

        # Очистка target_value для типа "yes_no"
        if type_ == 'yes_no':
            target_value = None
        else:
            try:
                target_value = float(target_value) if target_value else None
            except ValueError:
                logger.error(f"Неверное значение цели: {target_value}")
                return jsonify({"error": "Invalid target value"}), 400

        # Создание новой привычки
        habit = Habit(
            user_id=user_id,
            name=name,
            type=type_,
            target_value=target_value,
            period=period,
            color=color
        )
        db_session.add(habit)
        db_session.commit()

        logger.info(f"Пользователь {user_id} создал новую привычку: {name}")
        
        # Перенаправление на список привычек
        return redirect(url_for('habits.list_habits'))

    # Отображение формы (GET-запрос)
    logger.info(f"Пользователь {user_id} открыл страницу создания новой привычки.")
    return render_template('new.html')


@habits_bp.route('<int:habit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    user_id = session.get('user_id')
    logger.info(f"Пользователь {user_id} открывает или сохраняет изменения для привычки с ID {habit_id}.")

    habit = db_session.query(Habit).filter_by(id=habit_id, user_id=user_id).first()
    if not habit:
        logger.error(f"Привычка с ID {habit_id} не найдена для пользователя {user_id}.")
        return jsonify({"error": "Привычка не найдена"}), 404

    if request.method == 'POST':
        data = request.form
        habit.name = data.get('name', habit.name)
        habit.target_value = float(data.get('target_value')) if data.get('target_value') else None
        habit.color = data.get('color', habit.color)

        db_session.commit()
        logger.info(f"Привычка с ID {habit_id} успешно обновлена для пользователя {user_id}.")
        return redirect('/habits')

    # GET: отображение страницы редактирования
    logger.info(f"Пользователь {user_id} открыл страницу редактирования привычки с ID {habit_id}.")
    return render_template('edit_habit.html', habit=habit)



@habits_bp.route('/<int:habit_id>/delete', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """Удаление привычки"""
    user_id = session.get('user_id')
    logger.info(f"Пользователь {user_id} запросил удаление привычки с ID {habit_id}.")
    
    # Получение привычки
    habit = db_session.query(Habit).filter_by(id=habit_id, user_id=user_id).first()
    if not habit:
        logger.warning(f"Привычка с ID {habit_id} не найдена для пользователя {user_id}.")
        flash("Привычка не найдена!")
        return redirect(url_for('habits.list_habits'))

    # Удаление связанных логов
    db_session.query(HabitLog).filter_by(habit_id=habit.id).delete()
    logger.info(f"Все логи, связанные с привычкой {habit_id}, удалены.")

    # Удаление самой привычки
    db_session.delete(habit)
    db_session.commit()

    logger.info(f"Пользователь {user_id} успешно удалил привычку с ID {habit_id}.")
    flash("Привычка успешно удалена!")
    return redirect(url_for('habits.list_habits'))



@habits_bp.route('/<int:habit_id>/log', methods=['POST'])
@login_required
def toggle_habit_log(habit_id):
    user_id = session.get("user_id")
    logger.info(f"Пользователь {user_id} изменяет лог привычки с ID {habit_id}.")
    
    habit = db_session.query(Habit).filter_by(id=habit_id, user_id=user_id).first()
    if not habit:
        logger.error(f"Привычка с ID {habit_id} не найдена для пользователя {user_id}.")
        return jsonify({"error": "Привычка не найдена"}), 404

    data = request.json
    date_str = data.get("date")
    if not date_str:
        logger.error("Дата не передана в запросе.")
        return jsonify({"error": "Дата обязательна"}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.error("Неверный формат даты.")
        return jsonify({"error": "Неверный формат даты"}), 400

    log = db_session.query(HabitLog).filter_by(habit_id=habit.id, date=date).first()
    if not log:
        log = HabitLog(habit, date)
        db_session.add(log)

    if habit.type == "yes_no":
        log.is_completed = not log.is_completed
        log.value = 1 if log.is_completed else 0
    elif habit.type == "measurable":
        value = data.get("value", 0)
        try:
            value = int(value)  # Ограничение на целые числа
        except ValueError:
            logger.error("Введено некорректное значение.")
            return jsonify({"error": "Некорректное значение"}), 400
        

        log.value = value
        log.is_completed = value >= (habit.target_value or 0)

    db_session.commit()
    logger.info(f"Лог привычки {habit_id} для даты {date} успешно обновлен.")
    return jsonify({"message": "Лог обновлен успешно", "value": log.value})





@habits_bp.route('/<int:habit_id>/statistics', methods=['GET'])
@login_required
def get_habit_statistics(habit_id):
    user_id = session.get('user_id')
    if not user_id:
        logger.warning("Попытка неавторизованного доступа к статистике.")
        return jsonify({"error": "Unauthorized"}), 401

    # Получение привычки с использованием db_session
    habit = db_session.query(Habit).options(joinedload(Habit.logs)).filter_by(id=habit_id, user_id=user_id).first()
    if not habit:
        logger.warning(f"Привычка с ID {habit_id} не найдена для пользователя {user_id}.")
        return jsonify({"error": "Habit not found"}), 404

    # Получение текущей даты и формирование календаря
    current_date = datetime.now().date()
    start_of_month = current_date.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=31)).replace(day=1)

    logs = [log for log in habit.logs if start_of_month <= log.date < end_of_month]

    # Генерация данных для календаря
    calendar = []
    week = []
    for day in range(start_of_month.day, end_of_month.day):
        date = start_of_month + timedelta(days=day - 1)
        log = next((l for l in logs if l.date == date), None)
        calendar_day = {
            "date": date,
            "completed": log.is_completed if log else False,
            "is_today": date == current_date
        }
        week.append(calendar_day)

        # Завершение недели
        if len(week) == 7:
            calendar.append(week)
            week = []

    if week:
        calendar.append(week)

    # Подсчет стрика
    streak = 0
    for log in sorted(logs, key=lambda x: x.date, reverse=True):
        if log.is_completed:
            streak += 1
        else:
            break

    logger.info(f"Пользователь {user_id} просматривает статистику привычки {habit.name}.")

    # Рендеринг шаблона
    return render_template(
        "statistics.html",
        habit=habit,
        streak=streak,
        calendar=calendar
    )
