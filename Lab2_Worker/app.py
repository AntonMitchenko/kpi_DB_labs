import os
import time

import psycopg2
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from psycopg2 import OperationalError
import subprocess



# DB_CONFIG = {'user': 'postgres',
#              'password': 'AI3006',
#              'host': 'localhost',
#              'port': 5432,
#              'database': 'zno'}

DB_CONFIG = {'user': os.getenv("DB_USER"),
             'password': os.getenv("DB_PASSWORD"),
             'host': os.getenv("DB_HOST"),
             'port': os.getenv("DB_PORT"),
             'database': os.getenv("DB_NAME")}

SQLA_CONFIG_STR = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"




app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLA_CONFIG_STR
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()

from models import *

db.init_app(app)

migrate = Migrate(app, db)



def open_conn(db_config):
    """
    Функция open_conn принимает на вход конфигурацию базы данных db_config и устанавливает соединение с базой данных PostgreSQL.
    В случае неудачного подключения, функция повторяет попытку 3 раза с интервалом в 5 секунд между попытками.
    Если после 3 попыток соединение не установлено, то генерируется исключение.

    Аргументы:

    db_config (dict): словарь, содержащий параметры подключения к базе данных
    Возвращаемое значение:

    conn (psycopg2.extensions.connection): объект-соединение с базой данных
    """
    check = 3
    while check != 0:
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                dbname=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            break
        except OperationalError:
            print(f"Не удалось подключиться к базе данных {db_config['database']}. Попытка повторого подключения будет"
                  f" выполнена еще {check} раз(а)")
            time.sleep(5)
            check -= 1
            if check == 0:
                raise
    return conn




if __name__ == '__main__':
    start_time = time.time()


    def run_flask_db_upgrade():
        command = 'flask db upgrade'
        subprocess.call(command, shell=True)

    print("Розпочато міграцію...")
    run_flask_db_upgrade()



    fin_time = time.time() - start_time
    print(f"Час виконання програми: {fin_time} секунд ({round(fin_time / 60, 2)} хвилин) ")