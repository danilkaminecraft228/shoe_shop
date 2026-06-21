"""
Окно списка заказов.

Менеджер — только просмотр.
Администратор — просмотр + добавление/редактирование/удаление.

Ссылки на книгу "Python 3 и PyQt 6":
  - QTableWidget — гл. 23, разд. "Таблицы"
  - QPushButton — гл. 22, разд. "Кнопка"
  - QHeaderView — гл. 23, разд. "Заголовки таблицы"
  - QMessageBox — гл. 27, разд. "QMessageBox"
  - Работа с БД — гл. 24
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from utils.style import (
    COLOR_MAIN, COLOR_ACCENT, FONT_FAMILY, FONT_SIZE_TITLE, FONT_SIZE_DEFAULT,
    get_button_style
)
from utils.db_helpers import get_all_orders, delete_order


class OrdersWindow(QWidget):
    """
    Окно со списком заказов.

    role_id = 1 (администратор): полный CRUD.
    role_id = 2 (менеджер): только просмотр.
    """

    def __init__(self, user_data, on_back, on_order_edit):
        """
        user_data — dict с данными пользователя.
        on_back — функция возврата к списку товаров.
        on_order_edit — функция открытия формы заказа (для админа).
        """
        super().__init__()
        self.user_data = user_data
        self.role_id = user_data.get("role_id", 0)
        self.on_back = on_back
        self.on_order_edit = on_order_edit

        self._setup_ui()
        self._load_orders()

    def _setup_ui(self):
        """Настройка интерфейса."""
        self.setWindowTitle("Заказы — ООО «Обувь»")
        self.setGeometry(100, 100, 1100, 600)
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_MAIN}; color: #333333; font-family: '{FONT_FAMILY}'; }}")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Верхняя панель
        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_ACCENT};
                border-radius: 8px;
                padding: 8px;
            }}
            QLabel {{
                background-color: transparent;
                color: #E8F5E9;
            }}
        """)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        top_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel("Управление заказами")
        title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_TITLE, QFont.Weight.Bold))
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        # Информация о пользователе
        user_name = self.user_data.get("full_name", "Гость")
        name_label = QLabel(user_name)
        name_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        top_layout.addWidget(name_label)

        header_widget.setLayout(top_layout)
        main_layout.addWidget(header_widget)

        # ---- Кнопки ----
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        if self.role_id == 1:
            self.add_button = QPushButton("+ Добавить заказ")
            self.add_button.setStyleSheet(get_button_style(accent=True))
            self.add_button.clicked.connect(self._on_add_order)
            buttons_layout.addWidget(self.add_button)

        buttons_layout.addStretch()

        self.back_button = QPushButton("← Назад к товарам")
        self.back_button.setStyleSheet(get_button_style())
        self.back_button.clicked.connect(self._on_back)
        buttons_layout.addWidget(self.back_button)

        main_layout.addLayout(buttons_layout)

        # ---- Таблица заказов ----
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Номер заказа", "Состав заказа", "Статус",
            "Пункт выдачи", "Дата заказа", "Дата выдачи",
            "ФИО клиента", "Код получения"
        ])
        self.table.setStyleSheet("""
            QTableWidget {
                font-family: '%s';
                font-size: %dpt;
                border: 1px solid #CCCCCC;
                gridline-color: #DDDDDD;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                font-family: '%s';
                font-size: %dpt;
                font-weight: bold;
                background-color: %s;
                padding: 8px;
                border: 1px solid #CCCCCC;
            }
        """ % (FONT_FAMILY, FONT_SIZE_DEFAULT, FONT_FAMILY, FONT_SIZE_DEFAULT, COLOR_MAIN))

        # Настройка колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() + """
            QTableWidget { alternate-background-color: #F5FFF5; }
        """)

        # Двойной клик для редактирования (только админ)
        if self.role_id == 1:
            self.table.cellDoubleClicked.connect(self._on_edit_order)

        main_layout.addWidget(self.table, stretch=1)

        self.setLayout(main_layout)

    def _load_orders(self):
        """Загружает заказы в таблицу."""
        orders = get_all_orders()
        if not orders:
            self.table.setRowCount(0)
            return

        self.table.setRowCount(len(orders))

        for row_idx, order in enumerate(orders):
            # Номер заказа
            id_item = QTableWidgetItem(str(order["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, id_item)

            # Состав заказа
            items_text = order.get("items_info", "")
            self.table.setItem(row_idx, 1, QTableWidgetItem(items_text))

            # Статус
            status = order.get("status_name", "")
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 2, status_item)

            # Пункт выдачи
            address = order.get("pickup_address", "")
            self.table.setItem(row_idx, 3, QTableWidgetItem(address))

            # Дата заказа
            order_date = order.get("order_date")
            date_str = str(order_date) if order_date else ""
            self.table.setItem(row_idx, 4, QTableWidgetItem(date_str))

            # Дата доставки
            delivery_date = order.get("delivery_date")
            del_str = str(delivery_date) if delivery_date else ""
            self.table.setItem(row_idx, 5, QTableWidgetItem(del_str))

            # ФИО клиента
            client_name = order.get("client_name", "")
            self.table.setItem(row_idx, 6, QTableWidgetItem(client_name))

            # Код получения
            code = order.get("receive_code", "")
            self.table.setItem(row_idx, 7, QTableWidgetItem(code))

        self.table.resizeRowsToContents()

    def _on_add_order(self):
        """Открывает форму добавления заказа."""
        if self.role_id == 1:
            self.on_order_edit(None)

    def _on_edit_order(self, row, col):
        """Открывает форму редактирования заказа."""
        if self.role_id == 1:
            id_item = self.table.item(row, 0)
            if id_item:
                order_id = int(id_item.text())
                self.on_order_edit(order_id)

    def _on_back(self):
        """Возврат к списку товаров."""
        self.on_back()

    def refresh(self):
        """Обновляет данные таблицы."""
        self._load_orders()
