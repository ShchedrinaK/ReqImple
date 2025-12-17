from flask import Flask
from .extensions import db, login_manager
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['WTF_CSRF_ENABLED'] = False

    # Инициализируем расширения с приложением
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Импортируем и регистрируем blueprint ВНУТРИ функции
    from app.routers import bp
    app.register_blueprint(bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    """Загрузчик пользователя для Flask-Login"""
    from .models import User  # Импорт ВНУТРИ функции!
    return User.query.get(int(user_id))