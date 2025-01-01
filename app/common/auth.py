from flask import session, redirect, url_for, flash
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def login_required(func):
    """
    Декоратор для проверки авторизации пользователя перед доступом к определенным маршрутам.
    """
    @wraps(func)
    def wrapped_view(**kwargs):
        user_id = session.get('user_id')
        if not user_id:
            logger.warning("Попытка доступа без авторизации.")
            flash("Пожалуйста, авторизуйтесь для доступа к этому разделу.")
            return redirect(url_for('main.index'))
        return func(**kwargs)
    return wrapped_view
