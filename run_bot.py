import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Основная функция запуска"""
    from app import create_app
    from app.telegram_bot import run_bot_with_app

    # Создаем Flask приложение
    app = create_app()

    # Запускаем бота с приложением
    print("🚀 Запуск Telegram бота...")
    run_bot_with_app(app)


if __name__ == '__main__':
    main()