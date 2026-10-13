import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "smartpark.db")
SECRET_KEY = "smartpark-dev-secret-change-this"