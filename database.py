"""
Модуль подключения к базе данных MySQL.
Подключается к БД shoe_shop на локальном сервере.

Использование:
    connection = create_connection()
    # ... работа с БД ...
    close_connection(connection)

См. книгу "Python 3 и PyQt 6" гл. 24 (работа с базами данных).
"""

import mysql.connector
from mysql.connector import Error


def create_connection():
    """
    Создаёт и возвращает подключение к БД shoe_shop.
    В случае ошибки печатает сообщение и возвращает None.
    """
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            database="shoe_shop"
        )
        if connection.is_connected():
            print("Соединение с базой данных успешно установлено")
        return connection
    except Error as e:
        print(f"Ошибка подключения: {e}")
        return None


def close_connection(connection):
    """
    Закрывает подключение к БД, если оно активно.
    """
    if connection and connection.is_connected():
        connection.close()
        print("Соединение с базой данных закрыто")
