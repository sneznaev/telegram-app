from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from datetime import date, datetime
from app.common.database import db_session
from app.daily_review.models import DailyReviewState, DailyReviewQuestions, DailyReviewAnswers
from app.common.auth import login_required
from app.common.logger import logger

# Создаем Blueprint для модуля анализа итогов дня
daily_review_bp = Blueprint('daily_review', __name__, template_folder='templates', static_folder='static')

# Перечень предустановленных вопросов
PREDEFINED_QUESTIONS = [
    "Какова была моя цель?",
    "Что сегодня получилось особенно хорошо?",
    "С какими трудностями я столкнулся и как их преодолел?",
    "Чему я научился сегодня, какие были осознания?",
    "Какие эмоции я испытывал в течение дня и что их вызвало?",
    "Какие мои действия приблизили меня к моим целям?",
    "Что я мог бы сделать иначе для достижения лучших результатов?",
    "За что я сегодня благодарен?",
    "Как я заботился о своем физическом и эмоциональном здоровье?",
    "Какие моменты дня принесли мне радость или удовлетворение?",
    "Какие мысли или убеждения повлияли на мои решения сегодня?",
    "Какие задачи на завтра я перед собой ставлю, ведущие меня к моим целям"
]

# Роут для отображения и сохранения ежедневного отчета
@daily_review_bp.route('/', methods=['GET', 'POST'])
@login_required
def get_daily_review():
    user_id = session.get("user_id")
    
     # Инициализация предустановленных вопросов
    initialize_predefined_questions(user_id)
    
    
    selected_date = request.args.get('date')  # Дата из запроса
    try:
        if selected_date:
            # Конвертация строки в дату
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        else:
            selected_date = date.today()

        # Получаем отчет за выбранную дату, если он существует
        report = db_session.query(DailyReviewState).filter_by(user_id=user_id, date=selected_date).first()
        logger.info(f"Получаем отчет за выбранную дату: {report}")
        
        # Если отчет не найден и это POST-запрос, создаем новый
        if request.method == 'POST':
            energy_level = int(request.form.get('energy_level', 0))
            happiness_level = int(request.form.get('happiness_level', 0))
            stress_level = int(request.form.get('stress_level', 0))

            if not report:
                report = DailyReviewState(user_id=user_id, date=selected_date, energy_level=energy_level,
                                          happiness_level=happiness_level, stress_level=stress_level)
                db_session.add(report)

            report.energy_level = energy_level
            report.happiness_level = happiness_level
            report.stress_level = stress_level

            # Удаляем старые ответы и сохраняем новые
            db_session.query(DailyReviewAnswers).filter_by(report_id=report.id).delete()
            questions = db_session.query(DailyReviewQuestions).filter_by(user_id=user_id).all()
            for question in questions:
                answer_text = request.form.get(f'question_{question.id}', "")
                answer = DailyReviewAnswers(
                    user_id=user_id,
                    report_id=report.id,
                    question_id=question.id,
                    answer=answer_text
                )
                db_session.add(answer)

            db_session.commit()
            flash("Отчет успешно сохранен!", "success")
            return redirect(url_for('daily_review.get_daily_review', date=selected_date))

        # Получаем ответы на вопросы для текущего отчета
        answers = report.answers if report else []

        # Список дат с отчетами
        report_dates = [r.date.strftime('%Y-%m-%d') for r in db_session.query(DailyReviewState).filter_by(user_id=user_id).all()]

        # Загружаем список вопросов
        questions = db_session.query(DailyReviewQuestions).filter_by(user_id=user_id).all()
        return render_template(
            'daily_review.html', 
            report=report, 
            questions=questions, 
            answers=answers, 
            selected_date=selected_date,
            report_dates=report_dates
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке/сохранении отчета для пользователя {user_id}: {e}")
        flash("Ошибка при обработке отчета. Попробуйте снова.", "danger")
        return redirect(url_for('main.index'))


# Роут для настройки вопросов анализа
@daily_review_bp.route('/customize/', methods=['GET', 'POST'])
@login_required
def customize_questions():
    user_id = session.get("user_id")
    
    try:
        if request.method == 'POST':
            # Получение новых текстов вопросов
            question_texts = request.form.getlist('question_text')

            # Удаление старых вопросов
            db_session.query(DailyReviewQuestions).filter_by(user_id=user_id).delete()
            db_session.commit()

            # Добавление новых вопросов
            new_questions = [
                DailyReviewQuestions(user_id=user_id, question_text=text)
                for text in question_texts if text.strip()
            ]
            db_session.add_all(new_questions)
            db_session.commit()

            flash('Список вопросов успешно обновлен!', 'success')
            logger.info(f"Пользователь {user_id} обновил список вопросов.")
            return redirect(url_for('daily_review.customize_questions'))

        # Отображение текущих вопросов
        questions = db_session.query(DailyReviewQuestions).filter_by(user_id=user_id).all()
        return render_template('customize_questions.html', questions=questions)
    except Exception as e:
        logger.error(f"Ошибка при настройке вопросов для пользователя {user_id}: {e}")
        flash("Ошибка при настройке вопросов. Попробуйте снова.")
        return redirect(url_for('main.index'))

# Роут для удаления вопросов анализа        
@daily_review_bp.route('/delete-question', methods=['DELETE'])
@login_required
def delete_question():
    user_id = session.get("user_id")
    question_id = request.args.get('question_id')

    try:
        question = db_session.query(DailyReviewQuestions).filter_by(id=question_id, user_id=user_id).first()
        if question:
            db_session.delete(question)
            db_session.commit()
            logger.info(f"Пользователь {user_id} удалил вопрос с ID {question_id}.")
            return '', 204
        else:
            logger.warning(f"Пользователь {user_id} попытался удалить несуществующий вопрос с ID {question_id}.")
            return '', 404
    except Exception as e:
        logger.error(f"Ошибка при удалении вопроса для пользователя {user_id}: {e}")
        return '', 500

@daily_review_bp.route('/save-question', methods=['POST'])
@login_required
def save_question():
    user_id = session.get("user_id")
    data = request.get_json()
    question_id = request.args.get('question_id')
    question_text = data.get('question_text')

    try:
        question = db_session.query(DailyReviewQuestions).filter_by(id=question_id, user_id=user_id).first()
        if question:
            question.question_text = question_text
            db_session.commit()
            return '', 204
        return '', 404
    except Exception as e:
        logger.error(f"Ошибка при сохранении вопроса {question_id} для пользователя {user_id}: {e}")
        return '', 500

@daily_review_bp.route('/add-question', methods=['POST'])
@login_required
def add_question():
    user_id = session.get("user_id")
    data = request.get_json()
    question_text = data.get('question_text')

    try:
        new_question = DailyReviewQuestions(user_id=user_id, question_text=question_text)
        db_session.add(new_question)
        db_session.commit()
        return {'question_id': new_question.id}, 201
    except Exception as e:
        logger.error(f"Ошибка при добавлении нового вопроса для пользователя {user_id}: {e}")
        return '', 500


@daily_review_bp.route('/history/', methods=['GET'])
@login_required
def view_history():
    user_id = session.get("user_id")
    try:
        # Получение всех отчетов пользователя, отсортированных по дате
        reports = (
            db_session.query(DailyReviewState)
            .filter_by(user_id=user_id)
            .order_by(DailyReviewState.date.asc())
            .all()
        )

        # Проверяем, есть ли отчеты
        if not reports:
            flash("У вас еще нет сохраненных отчетов.", "info")
            return redirect(url_for('daily_review.get_daily_review'))

        # Подготовка данных для графиков
        chart_data = {
            "dates": [report.date.strftime('%d.%m.%Y') for report in reports],
            "energy_levels": [report.energy_level for report in reports],
            "happiness_levels": [report.happiness_level for report in reports],
            "stress_levels": [report.stress_level for report in reports],
        }

        # Подготовка данных для ответов на вопросы
        answers_by_date = {}
        for report in reports:
            answers = []
            for answer in report.answers:
                # Получаем текст вопроса из таблицы DailyReviewQuestions
                question = (
                    db_session.query(DailyReviewQuestions)
                    .filter_by(id=answer.question_id, user_id=user_id)
                    .first()
                )
                if question:
                    answers.append({
                        "question_text": question.question_text,
                        "answer": answer.answer,
                    })
                else:
                    logger.warning(f"Ответ с ID {answer.id} не связан с вопросом.")
            answers_by_date[report.date.strftime('%d.%m.%Y')] = answers

        # Логируем подготовленные данные
        logger.info(f"Данные для графиков: {chart_data}")
        logger.info(f"Ответы на вопросы: {answers_by_date}")

        # Подготовка ID отчетов
        report_ids = {report.date.strftime('%d.%m.%Y'): report.id for report in reports}

        # Рендеринг страницы
        return render_template(
            'history.html',
            chart_data=chart_data,
            answers_by_date=answers_by_date,
            report_ids=report_ids,
        )

    except Exception as e:
        logger.error(f"Ошибка при загрузке истории отчетов для пользователя {user_id}: {e}")
        flash("Ошибка при загрузке истории. Попробуйте снова.", "danger")
        return redirect(url_for('daily_review.get_daily_review'))




@daily_review_bp.route('/delete-report/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    user_id = session.get("user_id")  # Получаем ID пользователя из сессии
    try:
        # Ищем отчет по ID и проверяем, принадлежит ли он текущему пользователю
        report = db_session.query(DailyReviewState).filter_by(id=report_id, user_id=user_id).first()
        if report:
            # Удаляем все ответы на вопросы, связанные с этим отчетом (автоматически через связи)
            db_session.delete(report)
            db_session.commit()
            logger.info(f"Пользователь {user_id} удалил отчет за {report.date}.")
            flash("Отчет успешно удален!", "success")
        else:
            logger.warning(f"Пользователь {user_id} попытался удалить несуществующий отчет с ID {report_id}.")
            flash("Отчет не найден.", "warning")
    except Exception as e:
        logger.error(f"Ошибка при удалении отчета для пользователя {user_id}: {e}")
        flash("Произошла ошибка при удалении отчета. Попробуйте снова.", "danger")
    
    # Возвращаем пользователя на страницу истории
    return redirect(url_for('daily_review.view_history'))

# Предустановленные вопросы 
def initialize_predefined_questions(user_id):
    # Проверяем, есть ли вопросы в базе данных для текущего пользователя
    existing_questions = db_session.query(DailyReviewQuestions).filter_by(user_id=user_id).count()
    if existing_questions == 0:
        # Создаем предустановленные вопросы
        new_questions = [
            DailyReviewQuestions(user_id=user_id, question_text=question)
            for question in PREDEFINED_QUESTIONS
        ]
        db_session.add_all(new_questions)
        db_session.commit()
        logger.info(f"Предустановленные вопросы созданы для пользователя {user_id}.")
