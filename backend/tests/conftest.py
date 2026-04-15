import os
from pathlib import Path

os.environ['RESTAURANTS_DB_PATH'] = str(Path(__file__).resolve().parent / 'test_restaurants.db')
