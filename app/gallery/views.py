from flask import render_template, request, redirect, url_for, session, flash
from app.common.logger import logger
from app.common.database import db_session
from app.common.cloudinary_client import upload_to_cloudinary, delete_from_cloudinary
from app.common.auth import login_required
from app.common.models import Photo
from . import gallery_bp

@gallery_bp.route("/", methods=["GET"])
@login_required
def gallery():
    """Просмотр фотогалереи."""
    user_id = session.get("user_id")
    try:
        photos = db_session.query(Photo).filter_by(user_id=user_id).all()
        logger.info(f"Пользователь {user_id} просматривает галерею: найдено {len(photos)} фото.")
        return render_template("gallery.html", photos=photos)
    except Exception as e:
        logger.error(f"Ошибка при загрузке галереи для пользователя {user_id}: {e}")
        flash("Ошибка загрузки галереи. Попробуйте снова.")
        return redirect(url_for("main.index"))

@gallery_bp.route("/manage", methods=["GET", "POST"])
@login_required
def manage_photos():
    """Управление фотографиями."""
    user_id = session.get("user_id")

    if request.method == "POST":
        file = request.files.get("photo")
        caption = request.form.get("caption")

        if not file or not caption:
            flash("Пожалуйста, выберите файл и добавьте подпись.")
            return redirect(url_for("gallery.manage_photos"))

        if not file.content_type.startswith("image/"):
            flash("Можно загружать только изображения.")
            return redirect(url_for("gallery.manage_photos"))

        try:
            # Загрузка файла в Cloudinary
            result = upload_to_cloudinary(file, folder=f"user_uploads/{user_id}")
            photo = Photo(
                user_id=user_id,
                file_path=result["secure_url"],
                public_id=result["public_id"],
                caption=caption[:100]
            )
            db_session.add(photo)
            db_session.commit()
            flash("Фотография успешно добавлена.")
            logger.info(f"Пользователь {user_id} загрузил фото: {photo.file_path}")
        except Exception as e:
            logger.error(f"Ошибка загрузки изображения для пользователя {user_id}: {e}")
            flash("Ошибка загрузки изображения. Попробуйте снова.")

    photos = db_session.query(Photo).filter_by(user_id=user_id).all()
    return render_template("manage.html", photos=photos)

@gallery_bp.route("/delete/<int:photo_id>", methods=["POST"])
@login_required
def delete_photo(photo_id):
    """Удаление фотографии."""
    user_id = session.get("user_id")
    photo = db_session.query(Photo).filter_by(id=photo_id, user_id=user_id).first()

    if not photo:
        flash("Фотография не найдена.")
        return redirect(url_for("gallery.manage_photos"))

    try:
        delete_from_cloudinary(photo.public_id)
        db_session.delete(photo)
        db_session.commit()
        flash("Фотография успешно удалена.")
        logger.info(f"Пользователь {user_id} удалил фото с ID {photo_id}")
    except Exception as e:
        logger.error(f"Ошибка при удалении фото для пользователя {user_id}: {e}")
        flash("Ошибка удаления фотографии. Попробуйте снова.")

    return redirect(url_for("gallery.manage_photos"))
