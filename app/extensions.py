"""
Вынос расширений в отдельный файл для избежания циклических импортов.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
