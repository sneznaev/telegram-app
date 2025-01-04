from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from app.common.database import db_session
from app.common.logger import logger
from app.common.auth import login_required
from app.habits.models import Habit, HabitLog
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

habits_bp = Blueprint('habits', __name__, template_folder='templates', static_folder='static')


@habits_bp.route('/', methods=['GET'])
@login_required
def list_habits():
    """Главная страница с привычками"""
    user_id = session.get('user_id')
    habits = db_session.query(Habit).filter_by(user_id=user_id).all()
    current_date = datetime.utcnow().date()
    logger.info(f"Пользователь {user_id} открыл список привычек.")
    return render_template('habits.html', habits=habits, current_date=current_date)


from flask import redirect, url_for

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
    habit = db_session.query(Habit).filter_by(id=habit_id, user_id=user_id).first()
    if not habit:
        flash("Привычка не найдена!")
        logger.warning(f"Пользователь {user_id} попытался удалить несуществующую привычку с ID {habit_id}.")
        return redirect(url_for('habits.list_habits'))

    db_session.delete(habit)
    db_session.commit()

    logger.info(f"Пользователь {user_id} удалил привычку с ID {habit.id}.")
    flash("Привычка успешно удалена!")
    return redirect(url_for('habits.list_habits'))


@habits_bp.route('/<int:habit_id>/log', methods=['POST'])
@login_required
def log_habit(habit_id):
    """Фиксация выполнения привычки"""
    user_id = session.get('user_id')
    habit = db_session.query(Habit).filter_by(id=habit_id, user_id=user_id).first()
    if not habit:
        logger.warning(f"Пользователь {user_id} попытался зафиксировать выполнение несуществующей привычки с ID {habit_id}.")
        return jsonify({"error": "Привычка не найдена"}), 404

    data = request.json
    date = data.get('date')
    value = data.get('value')

    try:
        date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(f"Пользователь {user_id} указал некорректный формат даты: {date}.")
        return jsonify({"error": "Некорректный формат даты"}), 400

    log = HabitLog.query.filter_by(habit_id=habit_id, date=date).first()
    if not log:
        log = HabitLog(habit_id=habit_id, date=date, value=value)
        db_session.add(log)
    else:
        log.value = value
        log.is_completed = value is not None and (value >= habit.target_value if habit.type == 'measurable' else True)

    db_session.commit()
    logger.info(f"Пользователь {user_id} зафиксировал выполнение привычки с ID {habit_id} на дату {date}.")
    return jsonify({"message": "Фиксация успешна"}), 200



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
