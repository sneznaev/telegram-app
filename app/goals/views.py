from flask import render_template, request, redirect, url_for, session, flash
from app.common.logger import logger
from app.common.database import db_session
from app.common.auth import login_required
from app.common.models import Goal
from . import goals_bp

@goals_bp.route("/", methods=["GET"])
@login_required
def list_goals():
    """Просмотр списка целей."""
    user_id = session.get("user_id")
    try:
        goals = db_session.query(Goal).filter_by(user_id=user_id).order_by(Goal.is_completed, Goal.position).all()
        completed_goals = sum(goal.is_completed for goal in goals)
        total_goals = len(goals)
        logger.info(f"Пользователь {user_id} просматривает цели: всего {total_goals}, выполнено {completed_goals}.")
        return render_template("goals.html", goals=goals, total_goals=total_goals, completed_goals=completed_goals)
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка целей для пользователя {user_id}: {e}")
        flash("Ошибка загрузки целей. Попробуйте снова.")
        return redirect(url_for("main.index"))

@goals_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_goals():
    """Редактирование целей."""
    user_id = session.get("user_id")

    if request.method == "POST":
        action = request.form.get("action")
        logger.info(f"Получен POST-запрос с действием: {action}")

        if action == "add":
            text = request.form.get("text")
            if text and len(text) <= 250:
                max_position = db_session.query(Goal.position).filter_by(user_id=user_id).order_by(Goal.position.desc()).first()
                new_position = max_position[0] + 1 if max_position else 1
                goal = Goal(user_id=user_id, text=text, position=new_position)
                db_session.add(goal)
                db_session.commit()
                flash("Цель добавлена!")
                logger.info(f"Пользователь {user_id} добавил новую цель.")
            else:
                flash("Текст цели должен быть не длиннее 250 символов.")
                logger.warning(f"Некорректный текст цели от пользователя {user_id}.")

        elif action == "delete":
            goal_id = request.form.get("goal_id")
            goal = db_session.query(Goal).filter_by(id=goal_id, user_id=user_id).first()
            if goal:
                db_session.delete(goal)
                db_session.commit()
                flash("Цель удалена.")
                logger.info(f"Пользователь {user_id} удалил цель с ID {goal_id}.")
            else:
                flash("Цель не найдена.")
                logger.warning(f"Пользователь {user_id} пытался удалить несуществующую цель с ID {goal_id}.")

        elif action == "reorder":
            order = request.form.get("order")
            if order:
                order_list = map(int, order.split(","))
                try:
                    for index, goal_id in enumerate(order_list, start=1):
                        goal = db_session.query(Goal).filter_by(id=goal_id, user_id=user_id).first()
                        if goal:
                            goal.position = index
                    db_session.commit()
                    flash("Цели успешно отсортированы.")
                    logger.info(f"Пользователь {user_id} обновил порядок целей.")
                except Exception as e:
                    logger.error(f"Ошибка сортировки целей для пользователя {user_id}: {e}")
                    flash("Ошибка при сортировке целей. Попробуйте снова.")

        return redirect(url_for("goals.edit_goals"))

    goals = db_session.query(Goal).filter_by(user_id=user_id).order_by(Goal.position).all()
    return render_template("edit_goals.html", goals=goals)

@goals_bp.route("/complete/<int:goal_id>", methods=["POST"])
@login_required
def complete_goal(goal_id):
    """Переключение статуса выполнения цели."""
    user_id = session.get("user_id")
    goal = db_session.query(Goal).filter_by(id=goal_id, user_id=user_id).first()
    if goal:
        goal.is_completed = not goal.is_completed
        db_session.commit()
        flash("Статус цели обновлен.")
        logger.info(f"Пользователь {user_id} обновил статус цели с ID {goal_id}.")
    else:
        flash("Цель не найдена.")
        logger.warning(f"Пользователь {user_id} пытался обновить несуществующую цель с ID {goal_id}.")
    return redirect(url_for("goals.list_goals"))
