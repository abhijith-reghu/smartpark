import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "smartpark.db")

# Set SECRET_KEY in the environment for any real deployment.
SECRET_KEY = os.environ.get("SECRET_KEY", "smartpark-dev-secret-change-this")
