"""
Окно добавления / редактирования заказа.
Доступно только администратору.

Ссылки на книгу "Python 3 и PyQt 6":
  - QLabel — гл. 22, разд. "Надпись"
  - QLineEdit — гл. 22, разд. "Поле ввода"
  - QPushButton — гл. 22, разд. "Кнопка"
  - QComboBox — гл. 22, разд. "Выпадающий список"
  - QDateEdit — гл. 22, разд. "Редактор даты"
  - QTableWidget — гл. 23, разд. "Таблицы"
  - QMessageBox — гл. 27, разд. "QMessageBox"
  - Работа с БД — гл. 24
"""

import os
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSpinBox, QAbstractItemView, QGroupBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QDate

from utils.style import (
    COLOR_MAIN, FONT_FAMILY, FONT_SIZE_TITLE, FONT_SIZE_DEFAULT,
    get_button_style, get_line_edit_style, get_combo_box_style
)
from utils.db_helpers import (
    get_order_by_id, add_order, update_order, delete_order,
    get_all_clients, get_all_pickup_points, get_all_order_statuses,
    get_all_products
)


class OrderFormWindow(QWidget):
    """
    Окно добавления/редактирования заказа.
    Если order_id is None — режим добавления, иначе — редактирования.
    """

    def __init__(self, order_id=None, on_save=None, on_cancel=None):
        """
        order_id — ID заказа для редактирования или None.
        on_save — callback после сохранения.
        on_cancel — callback возврата.
        """
        super().__init__()
        self.order_id = order_id
        self.on_save = on_save
        self.on_cancel = on_cancel
        self._is_editing = order_id is not None

        # Список товаров в заказе: [{"product_id": ..., "article": ..., "name": ..., "quantity": ...}]
        self.order_items = []

        try:
            self._setup_ui()
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"Не удалось загрузить форму заказа:\n{e}"
            )
            if self.on_cancel:
                self.on_cancel()
            return

        if self._is_editing:
            self._load_order_data()

    def _setup_ui(self):
        """Настройка интерфейса формы."""
        title_text = "Редактирование заказа" if self._is_editing else "Добавление заказа"
        self.setWindowTitle(f"{title_text} — ООО «Обувь»")
        self.setGeometry(200, 100, 800, 700)
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_MAIN}; color: #333333; font-family: '{FONT_FAMILY}'; }}")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title_label = QLabel(title_text)
        title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_TITLE, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        # ---- Поля формы ----
        # Статус
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Статус заказа (*):"))
        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet(get_combo_box_style())
        self.status_combo.setMinimumWidth(200)
        self._load_combo(self.status_combo, get_all_order_statuses())
        form_layout.addWidget(self.status_combo)
        form_layout.addStretch()
        main_layout.addLayout(form_layout)

        # Пункт выдачи
        form_layout2 = QHBoxLayout()
        form_layout2.addWidget(QLabel("Пункт выдачи (*):"))
        self.pickup_combo = QComboBox()
        self.pickup_combo.setStyleSheet(get_combo_box_style())
        self.pickup_combo.setMinimumWidth(400)
        self._load_combo(self.pickup_combo, get_all_pickup_points(), "address")
        form_layout2.addWidget(self.pickup_combo)
        form_layout2.addStretch()
        main_layout.addLayout(form_layout2)

        # Клиент
        form_layout3 = QHBoxLayout()
        form_layout3.addWidget(QLabel("Клиент (*):"))
        self.client_combo = QComboBox()
        self.client_combo.setStyleSheet(get_combo_box_style())
        self.client_combo.setMinimumWidth(300)
        self._load_combo(self.client_combo, get_all_clients(), "full_name")
        form_layout3.addWidget(self.client_combo)
        form_layout3.addStretch()
        main_layout.addLayout(form_layout3)

        # Даты
        dates_layout = QHBoxLayout()
        dates_layout.setSpacing(20)

        date_layout1 = QVBoxLayout()
        date_layout1.addWidget(QLabel("Дата заказа (*):"))
        self.order_date_edit = QDateEdit()
        self.order_date_edit.setCalendarPopup(True)
        self.order_date_edit.setDate(QDate.currentDate())
        self.order_date_edit.setStyleSheet(get_line_edit_style())
        date_layout1.addWidget(self.order_date_edit)
        dates_layout.addLayout(date_layout1)

        date_layout2 = QVBoxLayout()
        date_layout2.addWidget(QLabel("Дата доставки:"))
        self.delivery_date_edit = QDateEdit()
        self.delivery_date_edit.setCalendarPopup(True)
        self.delivery_date_edit.setDate(QDate.currentDate().addDays(7))
        self.delivery_date_edit.setStyleSheet(get_line_edit_style())
        date_layout2.addWidget(self.delivery_date_edit)
        dates_layout.addLayout(date_layout2)

        dates_layout.addStretch()
        main_layout.addLayout(dates_layout)

        # Код получения
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("Код для получения:"))
        self.code_edit = QLineEdit()
        self.code_edit.setStyleSheet(get_line_edit_style())
        self.code_edit.setMaxLength(20)
        self.code_edit.setPlaceholderText("Код получения")
        self.code_edit.setMaximumWidth(200)
        code_layout.addWidget(self.code_edit)
        code_layout.addStretch()
        main_layout.addLayout(code_layout)

        # ---- Состав заказа ----
        items_group = QGroupBox("Состав заказа")
        items_group.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        items_group.setStyleSheet("""
            QGroupBox {
                font-family: '%s';
                font-size: %dpt;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """ % (FONT_FAMILY, FONT_SIZE_DEFAULT))
        items_layout = QVBoxLayout()

        # Панель добавления товара
        add_item_layout = QHBoxLayout()
        add_item_layout.setSpacing(10)

        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet(get_combo_box_style())
        self.product_combo.setMinimumWidth(250)
        # Загружаем товары: показываем "Артикул — Наименование"
        all_products = get_all_products()
        for p in all_products:
            display = f"{p['article']} — {p['name']}"
            self.product_combo.addItem(display, p["id"])
        add_item_layout.addWidget(self.product_combo)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setStyleSheet(get_line_edit_style())
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setValue(1)
        add_item_layout.addWidget(QLabel("Кол-во:"))
        add_item_layout.addWidget(self.quantity_spin)

        self.add_item_button = QPushButton("+ Добавить")
        self.add_item_button.setStyleSheet(get_button_style(accent=True))
        self.add_item_button.clicked.connect(self._add_item)
        add_item_layout.addWidget(self.add_item_button)

        add_item_layout.addStretch()
        items_layout.addLayout(add_item_layout)

        # Таблица состава заказа
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels([
            "Артикул", "Наименование", "Количество", ""
        ])
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        items_layout.addWidget(self.items_table)

        items_group.setLayout(items_layout)
        main_layout.addWidget(items_group, stretch=1)

        # ---- Кнопки ----
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.save_button = QPushButton("Сохранить заказ")
        self.save_button.setStyleSheet(get_button_style(accent=True))
        self.save_button.clicked.connect(self._on_save)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setStyleSheet(get_button_style())
        self.cancel_button.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()

        if self._is_editing:
            self.delete_button = QPushButton("Удалить заказ")
            self.delete_button.setStyleSheet("""
                QPushButton {
                    font-family: '%s';
                    font-size: %dpt;
                    background-color: #FF4444;
                    color: #F5F5F5;
                    border: 1px solid #CC0000;
                    border-radius: 6px;
                    padding: 8px 20px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #CC0000;
                }
            """ % (FONT_FAMILY, FONT_SIZE_DEFAULT))
            self.delete_button.clicked.connect(self._on_delete)
            buttons_layout.addWidget(self.delete_button)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def _load_combo(self, combo, data_list, name_field="name"):
        """Загружает данные в QComboBox."""
        combo.clear()
        for item in data_list:
            if name_field not in item:
                # Fallback: показываем первый доступный строковой ключ
                fallback = next((v for k, v in item.items() if k != "id"), "")
                combo.addItem(str(fallback), item.get("id"))
            else:
                combo.addItem(item[name_field], item["id"])

    def _load_order_data(self):
        """Загружает данные заказа в форму."""
        order = get_order_by_id(self.order_id)
        if not order:
            QMessageBox.critical(
                self, "Ошибка",
                f"Заказ с ID {self.order_id} не найден."
            )
            self._on_cancel()
            return

        # Статус
        status_id = order.get("status_id")
        if status_id:
            idx = self.status_combo.findData(status_id)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)

        # Пункт выдачи
        pp_id = order.get("pickup_point_id")
        if pp_id:
            idx = self.pickup_combo.findData(pp_id)
            if idx >= 0:
                self.pickup_combo.setCurrentIndex(idx)

        # Клиент
        client_id = order.get("client_id")
        if client_id:
            idx = self.client_combo.findData(client_id)
            if idx >= 0:
                self.client_combo.setCurrentIndex(idx)

        # Даты
        od = order.get("order_date")
        if od:
            if isinstance(od, date):
                self.order_date_edit.setDate(QDate(od.year, od.month, od.day))
        dd = order.get("delivery_date")
        if dd:
            if isinstance(dd, date):
                self.delivery_date_edit.setDate(QDate(dd.year, dd.month, dd.day))

        # Код
        self.code_edit.setText(order.get("receive_code", "") or "")

        # Состав заказа
        self.order_items = []
        for item in order.get("items", []):
            self.order_items.append({
                "product_id": item["product_id"],
                "article": item["article"],
                "name": item["name"],
                "quantity": item["quantity"],
            })
        self._refresh_items_table()

    def _add_item(self):
        """Добавляет товар в состав заказа."""
        product_id = self.product_combo.currentData()
        if product_id is None:
            return

        quantity = self.quantity_spin.value()

        # Проверяем, нет ли уже такого товара в заказе
        for item in self.order_items:
            if item["product_id"] == product_id:
                # Увеличиваем количество
                item["quantity"] += quantity
                self._refresh_items_table()
                return

        # Получаем данные товара
        current_text = self.product_combo.currentText()
        parts = current_text.split(" — ", 1)
        article = parts[0] if parts else ""
        name = parts[1] if len(parts) > 1 else ""

        self.order_items.append({
            "product_id": product_id,
            "article": article,
            "name": name,
            "quantity": quantity,
        })
        self._refresh_items_table()

    def _remove_item(self, row):
        """Удаляет товар из состава заказа."""
        if 0 <= row < len(self.order_items):
            del self.order_items[row]
            self._refresh_items_table()

    def _refresh_items_table(self):
        """Обновляет таблицу состава заказа."""
        self.items_table.setRowCount(len(self.order_items))

        for row_idx, item in enumerate(self.order_items):
            self.items_table.setItem(row_idx, 0, QTableWidgetItem(item["article"]))
            self.items_table.setItem(row_idx, 1, QTableWidgetItem(item["name"]))
            qty_item = QTableWidgetItem(str(item["quantity"]))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_table.setItem(row_idx, 2, qty_item)

            # Кнопка удаления
            remove_btn = QPushButton("✕")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6666;
                    color: #F5F5F5;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FF0000;
                }
            """)
            remove_btn.clicked.connect(lambda checked, r=row_idx: self._remove_item(r))
            self.items_table.setCellWidget(row_idx, 3, remove_btn)

    def _validate(self):
        """Проверяет корректность данных."""
        errors = []

        if self.status_combo.currentData() is None:
            errors.append("Выберите статус заказа.")

        if self.pickup_combo.currentData() is None:
            errors.append("Выберите пункт выдачи.")

        if self.client_combo.currentData() is None:
            errors.append("Выберите клиента.")

        if not self.order_items:
            errors.append("Добавьте хотя бы один товар в заказ.")

        if errors:
            QMessageBox.warning(
                self, "Ошибка валидации",
                "Пожалуйста, исправьте следующие ошибки:\n\n" + "\n".join(errors)
            )
            return False

        return True

    def _on_save(self):
        """Сохраняет заказ."""
        if not self._validate():
            return

        order_date = self.order_date_edit.date().toPyDate()
        delivery_date = self.delivery_date_edit.date().toPyDate()

        data = {
            "order_date": order_date,
            "delivery_date": delivery_date,
            "pickup_point_id": self.pickup_combo.currentData(),
            "client_id": self.client_combo.currentData(),
            "receive_code": self.code_edit.text().strip(),
            "status_id": self.status_combo.currentData(),
            "items": self.order_items,
        }

        try:
            if self._is_editing:
                update_order(self.order_id, data)
                msg = "Заказ успешно обновлён."
            else:
                new_id = add_order(data)
                msg = f"Заказ успешно добавлен (ID: {new_id})."

            QMessageBox.information(self, "Сохранение", msg)
            if self.on_save:
                self.on_save()

        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка сохранения",
                f"Не удалось сохранить заказ:\n{e}"
            )

    def _on_delete(self):
        """Удаляет заказ."""
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить заказ №{self.order_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_order(self.order_id)
            QMessageBox.information(self, "Удаление", "Заказ успешно удалён.")
            if self.on_save:
                self.on_save()
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка удаления",
                f"Не удалось удалить заказ:\n{e}"
            )

    def _on_cancel(self):
        """Возврат к списку заказов."""
        if self.on_cancel:
            self.on_cancel()
