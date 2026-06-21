"""
Точка входа в приложение информационной системы ООО «Обувь».
Запускает окно авторизации и управляет навигацией между окнами.

Демонстрационный экзамен 09.02.07-2-2026.

Ссылки на книгу "Python 3 и PyQt 6":
  - Окна PyQt6 — гл. 18–19
  - Сигналы и события — гл. 20
  - Работа с БД — гл. 24
  - QMessageBox — гл. 27, разд. "QMessageBox"
"""

import sys
import os

# Добавляем корневую папку проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QIcon

from database import create_connection, close_connection
from utils.style import FONT_FAMILY, WINDOW_STYLE
from ui.login_window import LoginWindow
from ui.products_window import ProductsWindow
from ui.product_form_window import ProductFormWindow
from ui.orders_window import OrdersWindow
from ui.order_form_window import OrderFormWindow


class Application:
    """
    Главный класс приложения.
    Управляет жизненным циклом окон и навигацией.
    """

    def __init__(self, app):
        self.app = app
        self.login_window = None
        self.products_window = None
        self.product_form_window = None
        self.orders_window = None
        self.order_form_window = None
        self.current_user = None

        # Устанавливаем общий стиль
        self.app.setStyleSheet(WINDOW_STYLE)

        # Устанавливаем иконку приложения
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "resources", "Icon.ico"
        )
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))

        # Проверяем подключение к БД при старте
        self._check_database_connection()

        # Запускаем окно входа
        self._show_login()

    def _check_database_connection(self):
        """Проверяет подключение к базе данных при запуске."""
        connection = create_connection()
        if not connection:
            QMessageBox.critical(
                None, "Ошибка подключения",
                "Не удалось подключиться к базе данных MySQL.\n\n"
                "Убедитесь, что:\n"
                "  • Сервер MySQL запущен\n"
                "  • База данных shoe_shop создана\n"
                "  • Параметры подключения верны (host=127.0.0.1, "
                "port=3306, user=root, password=root)\n\n"
                "Запустите schema.sql и seed_import.py для инициализации БД."
            )
        else:
            close_connection(connection)

    def _show_login(self):
        """Открывает окно авторизации."""
        self._close_all_windows()
        self.login_window = LoginWindow(on_login_success=self._on_login_success)
        self.login_window.show()

    def _on_login_success(self, user_data):
        """Обрабатывает успешный вход."""
        self.current_user = user_data
        self.login_window.close()
        self._show_products()

    def _show_products(self):
        """Открывает окно списка товаров."""
        self._close_all_windows()
        self.products_window = ProductsWindow(
            user_data=self.current_user,
            on_logout=self._show_login,
            on_orders_open=self._show_orders,
            on_product_edit=self._on_open_product_form
        )
        self.products_window.show()

    def _on_open_product_form(self, product_id):
        """
        Открывает форму товара.
        Если product_id is None — режим добавления.
        """
        if self.product_form_window is not None:
            QMessageBox.information(
                self.products_window, "Информация",
                "Окно редактирования товара уже открыто."
            )
            self.product_form_window.raise_()
            self.product_form_window.activateWindow()
            return

        self.product_form_window = ProductFormWindow(
            product_id=product_id,
            on_save=self._on_product_saved,
            on_cancel=self._on_product_form_closed
        )
        self.product_form_window.show()

    def _on_product_saved(self):
        """Обрабатывает сохранение/удаление товара."""
        self._on_product_form_closed()
        if self.products_window:
            self.products_window._refresh_products()

    def _on_product_form_closed(self):
        """Закрывает форму товара."""
        if self.product_form_window:
            self.product_form_window.close()
            self.product_form_window = None

    def _show_orders(self):
        """Открывает окно заказов."""
        self._close_all_windows(keep_products=False)
        self.orders_window = OrdersWindow(
            user_data=self.current_user,
            on_back=self._on_back_from_orders,
            on_order_edit=self._on_open_order_form
        )
        self.orders_window.show()

    def _on_back_from_orders(self):
        """Возврат к списку товаров из окна заказов."""
        self._close_all_windows(keep_products=False)
        self._show_products()

    def _on_open_order_form(self, order_id):
        """Открывает форму заказа."""
        self.order_form_window = OrderFormWindow(
            order_id=order_id,
            on_save=self._on_order_saved,
            on_cancel=self._on_order_form_closed
        )
        self.order_form_window.show()

    def _on_order_saved(self):
        """Обрабатывает сохранение/удаление заказа."""
        self._on_order_form_closed()
        if self.orders_window:
            self.orders_window.refresh()

    def _on_order_form_closed(self):
        """Закрывает форму заказа."""
        if self.order_form_window:
            self.order_form_window.close()
            self.order_form_window = None

    def _close_all_windows(self, keep_products=True):
        """
        Закрывает все открытые окна, кроме products_window при необходимости.
        """
        if self.product_form_window:
            self.product_form_window.close()
            self.product_form_window = None

        if self.order_form_window:
            self.order_form_window.close()
            self.order_form_window = None

        if not keep_products:
            if self.products_window:
                self.products_window.close()
                self.products_window = None

        if self.orders_window and not keep_products:
            self.orders_window.close()
            self.orders_window = None


def main():
    """Главная функция запуска приложения."""
    app = QApplication(sys.argv)
    app.setFont(QFont(FONT_FAMILY, 11))

    # Устанавливаем название приложения
    app.setApplicationName("ООО «Обувь» — Информационная система")

    # Запускаем приложение
    application = Application(app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
