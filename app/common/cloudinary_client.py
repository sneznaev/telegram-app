import os
import logging
from cloudinary.uploader import upload, destroy
from cloudinary import config

# Настройка Cloudinary через переменные окружения
config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

logger = logging.getLogger(__name__)

def upload_to_cloudinary(file, folder="default"):
    """
    Загружает файл в Cloudinary.
    
    :param file: Файл для загрузки.
    :param folder: Папка, куда будет загружен файл.
    :return: Ответ от Cloudinary API.
    """
    try:
        result = upload(file, folder=folder, use_filename=True, unique_filename=False)
        logger.info(f"Файл успешно загружен в Cloudinary: {result['secure_url']}")
        return result
    except Exception as e:
        logger.error(f"Ошибка загрузки файла в Cloudinary: {e}")
        raise

def delete_from_cloudinary(public_id):
    """
    Удаляет файл из Cloudinary.
    
    :param public_id: Public ID файла, который нужно удалить.
    :return: Ответ от Cloudinary API.
    """
    try:
        result = destroy(public_id)
        logger.info(f"Файл с ID {public_id} успешно удалён из Cloudinary.")
        return result
    except Exception as e:
        logger.error(f"Ошибка удаления файла с ID {public_id} из Cloudinary: {e}")
        raise
