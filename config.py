# config.py
import os

SECRET_KEY = os.urandom(24)
SQLALCHEMY_DATABASE_URI = 'sqlite:///task_manager.db'
TEMPLATES_AUTO_RELOAD = True
