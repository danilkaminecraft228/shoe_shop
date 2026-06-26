"""
Окно списка заказов.
Отображает заказы в виде карточек в QScrollArea.

Менеджер — только просмотр.
Администратор — просмотр + добавление/редактирование/удаление.

Ссылки на книгу "Python 3 и PyQt 6":
  - QScrollArea — гл. 21, разд. "Прокручиваемая панель"
  - QFrame — гл. 21, разд. "Рамка"
  - QLabel — гл. 22, разд. "Надпись"
  - QPushButton — гл. 22, разд. "Кнопка"
  - QDateEdit — гл. 22, разд. "Редактор даты и времени"
  - QLineEdit — гл. 22, разд. "Поле ввода"
  - QMessageBox — гл. 27, разд. "QMessageBox"
  - Работа с БД — гл. 24
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QDateEdit, QScrollArea,
    QFrame, QMessageBox, QGridLayout, QSizePolicy
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer, QDate

from utils.style import (
    COLOR_MAIN, COLOR_ACCENT, COLOR_ACCENT_LIGHT, COLOR_ACTION,
    COLOR_ACTION_HOVER, FONT_FAMILY,
    FONT_SIZE_DEFAULT, FONT_SIZE_TITLE, FONT_SIZE_CARD_TITLE, FONT_SIZE_SMALL,
    get_button_style, get_line_edit_style
)
from utils.db_helpers import (
    get_all_orders, get_filtered_orders, delete_order
)


class OrderCard(QFrame):
    """
    Карточка заказа для отображения в QScrollArea.

    Показывает номер заказа, статус, пункт выдачи,
    даты, ФИО клиента, состав заказа, код получения.
    """

    # Цвета статусов
    STATUS_COLORS = {
        "Новый": "#2196F3",
        "Подтверждён": "#FF9800",
        "Готов": "#9C27B0",
        "Выдан": "#4CAF50",
        "Отменён": "#F44336",
    }

    def __init__(self, order_data, parent=None, role_id=0,
                 on_edit=None, on_delete=None):
        """
        order_data — dict с данными заказа из БД.
        role_id — ID роли (1 = админ, 2 = менеджер).
        on_edit — функция редактирования заказа (для админа).
        on_delete — функция удаления заказа (для админа).
        """
        super().__init__(parent)
        self.order_data = order_data
        self.role_id = role_id
        self.on_edit = on_edit
        self.on_delete = on_delete
        self._setup_ui()

    def _setup_ui(self):
        """Создаёт содержимое карточки."""
        data = self.order_data
        status_name = data.get("status_name", "")
        status_color = self.STATUS_COLORS.get(status_name, "#757575")

        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_MAIN};
                border: 2px solid #CCCCCC;
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: #999999;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ---- Верхняя панель карточки (номер + статус) ----
        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_ACCENT};
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                padding: 6px 12px;
            }}
            QLabel {{
                background-color: transparent;
                color: #E8F5E9;
            }}
        """)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        header_layout.setContentsMargins(12, 6, 12, 6)

        # Номер заказа
        order_id = data.get("id", "")
        id_label = QLabel(f"Заказ №{order_id}")
        id_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_CARD_TITLE, QFont.Weight.Bold))
        header_layout.addWidget(id_label)

        header_layout.addStretch()

        # Статус
        status_badge = QLabel(f"  {status_name}  ")
        status_badge.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT, QFont.Weight.Bold))
        status_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {status_color};
                color: #FFFFFF;
                border-radius: 4px;
                padding: 2px 8px;
            }}
        """)
        status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(status_badge)

        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)

        # ---- Тело карточки ----
        body_widget = QWidget()
        body_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)

        body_layout = QVBoxLayout()
        body_layout.setSpacing(5)
        body_layout.setContentsMargins(15, 10, 15, 10)

        # Пункт выдачи
        address = data.get("pickup_address", "")
        self._add_field_row(body_layout, "Пункт выдачи:", address)

        # Вторая строка: дата заказа и код получения
        row2 = QHBoxLayout()
        row2.setSpacing(20)

        order_date = data.get("order_date")
        date_str = str(order_date) if order_date else "—"
        self._add_field_inline(row2, "Дата заказа:", date_str)

        code = data.get("receive_code", "")
        self._add_field_inline(row2, "Код получения:", code)
        body_layout.addLayout(row2)

        # Третья строка: ФИО клиента и дата выдачи
        row3 = QHBoxLayout()
        row3.setSpacing(20)

        client_name = data.get("client_name", "")
        self._add_field_inline(row3, "ФИО клиента:", client_name)

        delivery_date = data.get("delivery_date")
        del_str = str(delivery_date) if delivery_date else "—"
        self._add_field_inline(row3, "Дата выдачи:", del_str)
        body_layout.addLayout(row3)

        # Состав заказа
        items_text = data.get("items_info", "")
        self._add_field_row(body_layout, "Состав заказа:", items_text)

        body_widget.setLayout(body_layout)
        main_layout.addWidget(body_widget)

        # ---- Нижняя панель с кнопками действий ----
        if self.role_id == 1:
            actions_widget = QWidget()
            actions_widget.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                }
            """)

            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(15, 5, 15, 10)

            actions_layout.addStretch()

            # Кнопка редактирования
            edit_btn = QPushButton("✏️ Изменить")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    font-family: "{FONT_FAMILY}";
                    font-size: {FONT_SIZE_DEFAULT}pt;
                    background-color: {COLOR_ACTION};
                    color: #E8F5E9;
                    border: 1px solid #999999;
                    border-radius: 4px;
                    padding: 5px 12px;
                    min-height: 18px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_ACTION_HOVER};
                }}
            """)
            edit_btn.clicked.connect(self._on_edit)
            actions_layout.addWidget(edit_btn)

            # Кнопка удаления
            delete_btn = QPushButton("🗑️ Удалить")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    font-family: "{FONT_FAMILY}";
                    font-size: {FONT_SIZE_DEFAULT}pt;
                    background-color: #E53935;
                    color: #FFFFFF;
                    border: 1px solid #999999;
                    border-radius: 4px;
                    padding: 5px 12px;
                    min-height: 18px;
                }}
                QPushButton:hover {{
                    background-color: #C62828;
                }}
            """)
            delete_btn.clicked.connect(self._on_delete)
            actions_layout.addWidget(delete_btn)

            actions_widget.setLayout(actions_layout)
            main_layout.addWidget(actions_widget)

        self.setLayout(main_layout)

    def _add_field_row(self, layout, label, value):
        """Добавляет строку с label и value в вертикальный layout."""
        row = QHBoxLayout()
        row.setSpacing(5)
        name_label = QLabel(label)
        name_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #555555;")
        row.addWidget(name_label)

        value_label = QLabel(value)
        value_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        value_label.setWordWrap(True)
        row.addWidget(value_label, stretch=1)
        layout.addLayout(row)

    def _add_field_inline(self, layout, label, value):
        """Добавляет label + value в горизонтальный layout."""
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(4)

        name_label = QLabel(label)
        name_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #555555;")
        pair_layout.addWidget(name_label)

        value_label = QLabel(value)
        value_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        pair_layout.addWidget(value_label, stretch=1)

        layout.addLayout(pair_layout)

    def _on_edit(self):
        """Открывает форму редактирования заказа."""
        if self.role_id == 1 and self.on_edit:
            self.on_edit(self.order_data["id"])

    def _on_delete(self):
        """Удаляет заказ после подтверждения."""
        if self.role_id == 1 and self.on_delete:
            self.on_delete(self.order_data["id"])


class OrdersWindow(QWidget):
    """
    Окно со списком заказов (карточный формат).

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

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._load_orders)

        self._setup_ui()
        self._load_orders()

    def _setup_ui(self):
        """Настройка интерфейса."""
        self.setWindowTitle("Заказы — ООО «Обувь»")
        self.setGeometry(100, 100, 1100, 600)
        self.setStyleSheet(
            f"QWidget {{ background-color: {COLOR_MAIN}; "
            f"color: #333333; font-family: '{FONT_FAMILY}'; }}"
        )

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ---- Верхняя панель ----
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

        # ---- Фильтры (для ролей 1, 2) ----
        if self.role_id in (1, 2):
            filter_layout = QHBoxLayout()
            filter_layout.setSpacing(10)

            # Дата: С
            filter_layout.addWidget(QLabel("С:"))
            self.date_from_edit = QDateEdit()
            self.date_from_edit.setCalendarPopup(True)
            self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
            self.date_from_edit.setDisplayFormat("yyyy-MM-dd")
            self.date_from_edit.setStyleSheet(get_line_edit_style())
            self.date_from_edit.setMinimumWidth(120)
            self.date_from_edit.dateChanged.connect(self._on_filter_changed)
            filter_layout.addWidget(self.date_from_edit)

            # Дата: По
            filter_layout.addWidget(QLabel("По:"))
            self.date_to_edit = QDateEdit()
            self.date_to_edit.setCalendarPopup(True)
            self.date_to_edit.setDate(QDate.currentDate())
            self.date_to_edit.setDisplayFormat("yyyy-MM-dd")
            self.date_to_edit.setStyleSheet(get_line_edit_style())
            self.date_to_edit.setMinimumWidth(120)
            self.date_to_edit.dateChanged.connect(self._on_filter_changed)
            filter_layout.addWidget(self.date_to_edit)

            # Поиск
            filter_layout.addWidget(QLabel("Поиск:"))
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText("№ заказа, клиент, адрес...")
            self.search_edit.setStyleSheet(get_line_edit_style())
            self.search_edit.setMinimumWidth(200)
            self.search_edit.textChanged.connect(self._on_search_changed)
            filter_layout.addWidget(self.search_edit)

            filter_layout.addStretch()
            main_layout.addLayout(filter_layout)

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

        # ---- ScrollArea с карточками заказов ----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: #F5F5F5;
            }
            QScrollBar:vertical {
                width: 12px;
            }
        """)

        # Контейнер для карточек
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.addStretch()
        self.scroll_content.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, stretch=1)

        self.setLayout(main_layout)

    def _on_search_changed(self):
        """Поиск с задержкой (300 мс)."""
        self._search_timer.start(300)

    def _on_filter_changed(self):
        """Изменение даты фильтра — сразу обновляем."""
        self._load_orders()

    def _load_orders(self):
        """Загружает заказы в виде карточек."""
        # Определяем параметры фильтрации
        if self.role_id in (1, 2):
            search_text = self.search_edit.text().strip()
            date_from = self.date_from_edit.date().toString("yyyy-MM-dd")
            date_to = self.date_to_edit.date().toString("yyyy-MM-dd")
            orders = get_filtered_orders(search_text, date_from, date_to)
        else:
            orders = get_all_orders()

        # Очищаем старые карточки (кроме stretch)
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not orders:
            no_data_label = QLabel("Заказы не найдены")
            no_data_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("color: #888888; padding: 50px;")
            self.scroll_layout.insertWidget(0, no_data_label)
        else:
            for order in orders:
                card = OrderCard(
                    order,
                    role_id=self.role_id,
                    on_edit=self.on_order_edit if self.role_id == 1 else None,
                    on_delete=self._delete_order if self.role_id == 1 else None,
                )
                self.scroll_layout.insertWidget(
                    self.scroll_layout.count() - 1, card
                )

    def _delete_order(self, order_id):
        """Удаляет заказ после подтверждения."""
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить заказ №{order_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_order(order_id)
                self._load_orders()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось удалить заказ: {str(e)}"
                )

    def _on_add_order(self):
        """Открывает форму добавления заказа."""
        if self.role_id == 1:
            self.on_order_edit(None)

    def _on_back(self):
        """Возврат к списку товаров."""
        self.on_back()

    def refresh(self):
        """Обновляет список карточек."""
        self._load_orders()
