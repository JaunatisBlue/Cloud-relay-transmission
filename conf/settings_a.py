import os

IP = '127.0.0.1'
PORT = 8000
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_PATH, 'db')
CLIENT_DB_PATH = os.path.join(DB_PATH, 'A')
SERVER_DB_PATH = os.path.join(DB_PATH, 'A')
LOG_PATH = os.path.join(BASE_PATH, 'log')





