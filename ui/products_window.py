"""
Окно списка товаров.
Отображает карточки товаров в QScrollArea.
Включает поиск, сортировку, фильтрацию для соответствующих ролей.

Ссылки на книгу "Python 3 и PyQt 6":
  - QScrollArea — гл. 21, разд. "Прокручиваемая панель"
  - QLabel — гл. 22, разд. "Надпись"
  - QPushButton — гл. 22, разд. "Кнопка"
  - QLineEdit — гл. 22, разд. "Поле ввода"
  - QComboBox — гл. 22, разд. "Выпадающий список"
  - QMessageBox — гл. 27, разд. "QMessageBox"
  - QFrame — гл. 21, разд. "Рамка"
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QScrollArea,
    QFrame, QMessageBox, QGridLayout, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer

from database import create_connection
from utils.style import (
    COLOR_MAIN, COLOR_ACTION, COLOR_ACCENT, COLOR_ACCENT_LIGHT,
    COLOR_DISCOUNT_HIGH, COLOR_OUT_OF_STOCK,
    COLOR_PRICE_CROSSED, FONT_FAMILY,
    FONT_SIZE_DEFAULT, FONT_SIZE_TITLE, FONT_SIZE_CARD_TITLE, FONT_SIZE_SMALL,
    get_button_style, get_line_edit_style, get_combo_box_style,
    get_card_frame_style, get_label_style
)
from utils.db_helpers import (
    get_filtered_products, get_all_suppliers, get_all_products
)

# Размер фото товара в карточке
PHOTO_WIDTH = 150
PHOTO_HEIGHT = 150


class ProductCard(QFrame):
    """
    Карточка товара для отображения в QScrollArea.
    Содержит фото, категорию, наименование, описание,
    производителя, поставщика, цену, скидку.
    """

    def __init__(self, product_data, parent=None, role_id=0):
        """
        product_data — dict с данными товара из БД.
        role_id — ID роли для определения прав.
        """
        super().__init__(parent)
        self.product_data = product_data
        self.role_id = role_id
        self._setup_ui()

    def _setup_ui(self):
        """Создаёт содержимое карточки."""
        data = self.product_data
        has_discount = data.get("discount", 0) > 15
        out_of_stock = data.get("stock_quantity", 0) <= 0

        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(get_card_frame_style(has_discount, out_of_stock))

        # Основной горизонтальный layout карточки
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ---- Левая колонка: фото ----
        photo_label = QLabel()
        photo_label.setFixedSize(PHOTO_WIDTH, PHOTO_HEIGHT)
        photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_label.setStyleSheet("background-color: #F0F0F0; border-radius: 4px;")

        image_path = data.get("image_path")
        if image_path:
            # Ищем фото в resources/products
            img_full = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "resources", "products", image_path
            )
            if os.path.exists(img_full):
                pixmap = QPixmap(img_full)
                scaled = pixmap.scaled(
                    PHOTO_WIDTH - 10, PHOTO_HEIGHT - 10,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                photo_label.setPixmap(scaled)
            else:
                photo_label.setText("Нет фото")
        else:
            # Показываем picture.png
            placeholder = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "resources", "picture.png"
            )
            if os.path.exists(placeholder):
                pixmap = QPixmap(placeholder)
                scaled = pixmap.scaled(
                    PHOTO_WIDTH - 10, PHOTO_HEIGHT - 10,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                photo_label.setPixmap(scaled)
            else:
                photo_label.setText("Нет фото")

        main_layout.addWidget(photo_label)

        # ---- Центр: информация о товаре ----
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Категория
        category_label = QLabel(f"Категория: {data.get('category_name', '')}")
        category_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SMALL))
        category_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(category_label)

        # Наименование
        name_label = QLabel(data.get("name", ""))
        name_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_CARD_TITLE, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)

        # Артикул
        article_label = QLabel(f"Артикул: {data.get('article', '')}")
        article_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        info_layout.addWidget(article_label)

        # Описание
        description = data.get("description", "")
        if description:
            desc_label = QLabel(description[:200] + ("..." if len(description) > 200 else ""))
            desc_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #444444;")
            info_layout.addWidget(desc_label)

        # Производитель и поставщик в одну строку
        mfg_label = QLabel(
            f"Производитель: {data.get('manufacturer_name', '')} | "
            f"Поставщик: {data.get('supplier_name', '')}"
        )
        mfg_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SMALL))
        mfg_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(mfg_label)

        # Остаток на складе
        stock_label = QLabel(f"В наличии: {data.get('stock_quantity', 0)} {data.get('unit', 'шт.')}")
        stock_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        if data.get("stock_quantity", 0) <= 0:
            stock_label.setStyleSheet("color: #0066CC; font-weight: bold;")
        info_layout.addWidget(stock_label)

        info_layout.addStretch()
        main_layout.addLayout(info_layout, stretch=1)

        # ---- Правая колонка: цена и скидка ----
        price_layout = QVBoxLayout()
        price_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_layout.setSpacing(5)

        price = float(data.get("price", 0))
        discount = float(data.get("discount", 0))
        final_price = price - price * discount / 100

        # Единица измерения
        unit_label = QLabel(f"за {data.get('unit', 'шт.')}")
        unit_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SMALL))
        unit_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        unit_label.setStyleSheet("color: #888888;")
        price_layout.addWidget(unit_label)

        if discount > 0:
            # Перечёркнутая оригинальная цена
            original_price_label = QLabel(f"{price:,.2f} ₽".replace(",", " "))
            original_price_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_CARD_TITLE))
            original_price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            original_price_label.setStyleSheet(
                f"color: {COLOR_PRICE_CROSSED}; text-decoration: line-through;"
            )
            price_layout.addWidget(original_price_label)

            # Скидка
            discount_label = QLabel(f"-{discount:.0f}%")
            discount_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT, QFont.Weight.Bold))
            discount_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            discount_label.setStyleSheet(f"color: {COLOR_PRICE_CROSSED};")
            price_layout.addWidget(discount_label)

        # Итоговая цена
        final_price_label = QLabel(f"{final_price:,.2f} ₽".replace(",", " "))
        final_price_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_CARD_TITLE + 3, QFont.Weight.Bold))
        final_price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        final_price_label.setStyleSheet("color: #000000;")
        price_layout.addWidget(final_price_label)

        price_layout.addStretch()
        main_layout.addLayout(price_layout)

        self.setLayout(main_layout)
        self.setMinimumHeight(PHOTO_HEIGHT + 30)


class ProductsWindow(QWidget):
    """
    Главное окно со списком товаров.

    Роли:
      - Гость (0): просмотр без поиска/фильтрации
      - Авторизованный клиент (3): просмотр без поиска/фильтрации
      - Менеджер (2): просмотр с поиском/фильтрацией/сортировкой, доступ к заказам
      - Администратор (1): всё как у менеджера + CRUD товаров
    """

    def __init__(self, user_data, on_logout, on_orders_open, on_product_edit):
        """
        user_data — dict с данными пользователя.
        on_logout — функция выхода (закрывает окно и открывает login).
        on_orders_open — функция открытия окна заказов.
        on_product_edit — функция открытия формы товара (для админа).
        """
        super().__init__()
        self.user_data = user_data
        self.on_logout = on_logout
        self.on_orders_open = on_orders_open
        self.on_product_edit = on_product_edit
        self.role_id = user_data.get("role_id", 0)

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._refresh_products)

        self._setup_ui()
        self._refresh_products()

    def _setup_ui(self):
        """Настройка интерфейса."""
        self.setWindowTitle("Список товаров — ООО «Обувь»")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_MAIN}; color: #333333; font-family: '{FONT_FAMILY}'; }}")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ---- Верхняя панель с логотипом, заголовком и пользователем ----
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

        # Логотип
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources", "Icon.png"
        )
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled)
            top_layout.addWidget(logo_label)

        # Заголовок
        title_label = QLabel("ООО «Обувь» — Список товаров")
        title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_TITLE, QFont.Weight.Bold))
        top_layout.addWidget(title_label, stretch=1)

        # Информация о пользователе (справа)
        user_layout = QVBoxLayout()
        user_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        user_name = self.user_data.get("full_name", "Гость")
        name_label = QLabel(user_name)
        name_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        user_layout.addWidget(name_label)

        role_label = QLabel(f"Роль: {self.user_data.get('role_name', 'Гость')}")
        role_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SMALL))
        role_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        role_label.setStyleSheet("color: #C8E6C9; background-color: transparent;")
        user_layout.addWidget(role_label)

        top_layout.addLayout(user_layout)
        header_widget.setLayout(top_layout)
        main_layout.addWidget(header_widget)

        # ---- Панель управления (поиск, фильтр, сортировка) ----
        can_search = self.role_id in (1, 2)  # Менеджер или админ

        if can_search:
            search_layout = QHBoxLayout()
            search_layout.setSpacing(10)

            # Поиск
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText("Поиск товаров...")
            self.search_edit.setStyleSheet(get_line_edit_style())
            self.search_edit.setMinimumWidth(300)
            self.search_edit.textChanged.connect(self._on_search_changed)
            search_layout.addWidget(self.search_edit)

            # Фильтр по поставщику
            self.supplier_combo = QComboBox()
            self.supplier_combo.setStyleSheet(get_combo_box_style())
            self.supplier_combo.setMinimumWidth(200)
            self.supplier_combo.currentIndexChanged.connect(self._on_filter_changed)
            search_layout.addWidget(QLabel("Поставщик:"))
            search_layout.addWidget(self.supplier_combo)

            search_layout.addStretch()

            # Сортировка
            sort_label = QLabel("Сортировка по остатку:")
            sort_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
            search_layout.addWidget(sort_label)

            self.sort_combo = QComboBox()
            self.sort_combo.setStyleSheet(get_combo_box_style())
            self.sort_combo.addItems(["Без сортировки", "По возрастанию", "По убыванию"])
            self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
            search_layout.addWidget(self.sort_combo)

            main_layout.addLayout(search_layout)

        if can_search:
            # Загружаем поставщиков для фильтра
            self._load_suppliers()

        # ---- Кнопки действий ----
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Добавить товар (только админ, role_id = 1)
        if self.role_id == 1:
            self.add_button = QPushButton("+ Добавить товар")
            self.add_button.setStyleSheet(get_button_style(accent=True))
            self.add_button.clicked.connect(self._on_add_product)
            buttons_layout.addWidget(self.add_button)

        # Заказы (менеджер и админ)
        if self.role_id in (1, 2):
            self.orders_button = QPushButton("Заказы")
            self.orders_button.setStyleSheet(get_button_style())
            self.orders_button.clicked.connect(self._on_orders)
            buttons_layout.addWidget(self.orders_button)

        buttons_layout.addStretch()

        # Выход
        self.logout_button = QPushButton("Выйти")
        self.logout_button.setStyleSheet(get_button_style())
        self.logout_button.clicked.connect(self._on_logout)
        buttons_layout.addWidget(self.logout_button)

        main_layout.addLayout(buttons_layout)

        # ---- ScrollArea с карточками товаров ----
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

    def _load_suppliers(self):
        """Загружает список поставщиков в комбобокс фильтра."""
        self.supplier_combo.blockSignals(True)
        self.supplier_combo.clear()
        self.supplier_combo.addItem("Все поставщики", None)
        suppliers = get_all_suppliers()
        for s in suppliers:
            self.supplier_combo.addItem(s["name"], s["id"])
        self.supplier_combo.blockSignals(False)

    def _on_search_changed(self):
        """Поиск с задержкой (реальное время)."""
        self._search_timer.start(300)

    def _on_filter_changed(self):
        """Изменение фильтра по поставщику."""
        self._refresh_products()

    def _on_sort_changed(self):
        """Изменение сортировки."""
        self._refresh_products()

    def _refresh_products(self):
        """Обновляет список карточек товаров."""
        # Определяем параметры поиска/фильтрации
        can_search = self.role_id in (1, 2)

        if can_search:
            search_text = self.search_edit.text().strip()
            sup_id = self.supplier_combo.currentData()
            sort_idx = self.sort_combo.currentIndex()
            sort_order = ""
            if sort_idx == 1:
                sort_order = "asc"
            elif sort_idx == 2:
                sort_order = "desc"
        else:
            search_text = ""
            sup_id = None
            sort_order = ""

        # Очищаем старые карточки (кроме stretch)
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Загружаем товары
        if can_search:
            products = get_filtered_products(search_text, sup_id, sort_order)
        else:
            products = get_all_products()

        if not products:
            no_data_label = QLabel("Товары не найдены")
            no_data_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("color: #888888; padding: 50px;")
            self.scroll_layout.insertWidget(0, no_data_label)
        else:
            for p in products:
                card = ProductCard(p, role_id=self.role_id)
                # Для администратора клик по карточке открывает редактирование
                if self.role_id == 1:
                    card.mousePressEvent = lambda e, pid=p["id"]: self._on_edit_product(pid)
                self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)

    def _on_add_product(self):
        """Открывает форму добавления товара."""
        if self.role_id == 1:
            self.on_product_edit(None)

    def _on_edit_product(self, product_id):
        """Открывает форму редактирования товара."""
        if self.role_id == 1:
            self.on_product_edit(product_id)

    def _on_orders(self):
        """Открывает окно заказов."""
        self.on_orders_open()

    def _on_logout(self):
        """Выход из системы."""
        self.on_logout()
