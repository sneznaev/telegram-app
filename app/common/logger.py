import logging
import sys

def setup_logger():
    """
    Настраивает логирование для всего приложения.
    Логи выводятся в консоль.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Логи в консоль
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Логирование успешно настроено.")
    return logger

# Создаем глобальный объект logger
logger = setup_logger()
