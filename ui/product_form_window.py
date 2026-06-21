"""
Окно добавления / редактирования товара.
Доступно только администратору.

Ссылки на книгу "Python 3 и PyQt 6":
  - QLabel — гл. 22, разд. "Надпись"
  - QLineEdit — гл. 22, разд. "Поле ввода"
  - QPushButton — гл. 22, разд. "Кнопка"
  - QComboBox — гл. 22, разд. "Выпадающий список"
  - QTextEdit — гл. 22, разд. "Многострочное поле"
  - QFileDialog — гл. 27, разд. "Диалоги выбора файлов"
  - QMessageBox — гл. 27, разд. "QMessageBox"
  - Работа с БД — гл. 24
"""

import os
import shutil
from PIL import Image

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTextEdit,
    QMessageBox, QFileDialog, QScrollArea, QFrame,
    QDoubleSpinBox, QSpinBox, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt

from utils.style import (
    COLOR_MAIN, FONT_FAMILY, FONT_SIZE_TITLE, FONT_SIZE_DEFAULT,
    get_button_style, get_line_edit_style, get_combo_box_style
)
from utils.db_helpers import (
    get_product_by_id, add_product, update_product, delete_product,
    get_all_categories, get_all_manufacturers, get_all_suppliers
)


MAX_IMAGE_WIDTH = 300
MAX_IMAGE_HEIGHT = 200
PRODUCTS_IMG_DIR = None  # будет инициализировано при создании окна


class ProductFormWindow(QWidget):
    """
    Окно добавления/редактирования товара.
    Если product_id is None — режим добавления, иначе — редактирования.
    """

    def __init__(self, product_id=None, on_save=None, on_cancel=None):
        """
        product_id — ID товара для редактирования или None для нового.
        on_save — функция обратного вызова после успешного сохранения.
        on_cancel — функция возврата к списку товаров.
        """
        super().__init__()
        self.product_id = product_id
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.current_image_path = None  # путь к загруженному/существующему фото
        self._is_editing = product_id is not None

        global PRODUCTS_IMG_DIR
        PRODUCTS_IMG_DIR = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources", "products"
        )

        self._setup_ui()

        if self._is_editing:
            self._load_product_data()

    def _setup_ui(self):
        """Настройка интерфейса формы."""
        title_text = "Редактирование товара" if self._is_editing else "Добавление товара"
        self.setWindowTitle(f"{title_text} — ООО «Обувь»")
        self.setGeometry(200, 200, 650, 700)
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_MAIN}; color: #333333; font-family: '{FONT_FAMILY}'; }}")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title_label = QLabel(title_text)
        title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_TITLE, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        # Scroll area для формы
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        form_container = QWidget()
        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)

        # ID товара (только для редактирования)
        if self._is_editing:
            id_layout = QHBoxLayout()
            id_layout.addWidget(QLabel("ID товара:"))
            self.id_label = QLabel()
            self.id_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT, QFont.Weight.Bold))
            id_layout.addWidget(self.id_label)
            id_layout.addStretch()
            form_layout.addLayout(id_layout)

        # Фото товара
        photo_label = QLabel("Фото товара:")
        photo_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        form_layout.addWidget(photo_label)

        photo_layout = QHBoxLayout()
        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(MAX_IMAGE_WIDTH + 10, MAX_IMAGE_HEIGHT + 10)
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setStyleSheet(
            "background-color: #F0F0F0; border: 1px solid #CCCCCC; border-radius: 4px;"
        )
        self.photo_preview.setText("Нет изображения")
        photo_layout.addWidget(self.photo_preview)

        photo_buttons = QVBoxLayout()
        self.load_photo_button = QPushButton("Загрузить фото")
        self.load_photo_button.setStyleSheet(get_button_style())
        self.load_photo_button.clicked.connect(self._load_photo)
        photo_buttons.addWidget(self.load_photo_button)

        self.clear_photo_button = QPushButton("Удалить фото")
        self.clear_photo_button.setStyleSheet(get_button_style())
        self.clear_photo_button.clicked.connect(self._clear_photo)
        photo_buttons.addWidget(self.clear_photo_button)
        photo_buttons.addStretch()

        photo_layout.addLayout(photo_buttons)
        photo_layout.addStretch()
        form_layout.addLayout(photo_layout)

        # Артикул
        form_layout.addWidget(QLabel("Артикул товара (*):"))
        self.article_edit = QLineEdit()
        self.article_edit.setPlaceholderText("Например: А112Т4")
        self.article_edit.setStyleSheet(get_line_edit_style())
        form_layout.addWidget(self.article_edit)

        # Наименование
        form_layout.addWidget(QLabel("Наименование товара (*):"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Наименование товара")
        self.name_edit.setStyleSheet(get_line_edit_style())
        form_layout.addWidget(self.name_edit)

        # Категория
        form_layout.addWidget(QLabel("Категория товара (*):"))
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(get_combo_box_style())
        self._load_combo_data(self.category_combo, get_all_categories())
        form_layout.addWidget(self.category_combo)

        # Описание
        form_layout.addWidget(QLabel("Описание товара:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setStyleSheet("""
            QTextEdit {
                font-family: '%s';
                font-size: %dpt;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
            }
        """ % (FONT_FAMILY, FONT_SIZE_DEFAULT))
        form_layout.addWidget(self.description_edit)

        # Производитель
        form_layout.addWidget(QLabel("Производитель (*):"))
        self.manufacturer_combo = QComboBox()
        self.manufacturer_combo.setStyleSheet(get_combo_box_style())
        self.manufacturer_combo.setEditable(True)
        self._load_combo_data(self.manufacturer_combo, get_all_manufacturers())
        form_layout.addWidget(self.manufacturer_combo)

        # Поставщик
        form_layout.addWidget(QLabel("Поставщик (*):"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.setStyleSheet(get_combo_box_style())
        self._load_combo_data(self.supplier_combo, get_all_suppliers())
        form_layout.addWidget(self.supplier_combo)

        # Цена и единица измерения в одной строке
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)

        price_layout = QVBoxLayout()
        price_layout.addWidget(QLabel("Цена (*):"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setStyleSheet(get_line_edit_style())
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("₽ ")
        price_layout.addWidget(self.price_spin)
        row_layout.addLayout(price_layout)

        unit_layout = QVBoxLayout()
        unit_layout.addWidget(QLabel("Единица измерения:"))
        self.unit_edit = QLineEdit("шт.")
        self.unit_edit.setStyleSheet(get_line_edit_style())
        self.unit_edit.setMaxLength(20)
        unit_layout.addWidget(self.unit_edit)
        row_layout.addLayout(unit_layout)

        form_layout.addLayout(row_layout)

        # Количество и скидка в одной строке
        row_layout2 = QHBoxLayout()
        row_layout2.setSpacing(15)

        stock_layout = QVBoxLayout()
        stock_layout.addWidget(QLabel("Количество на складе (*):"))
        self.stock_spin = QSpinBox()
        self.stock_spin.setStyleSheet(get_line_edit_style())
        self.stock_spin.setRange(0, 999999)
        stock_layout.addWidget(self.stock_spin)
        row_layout2.addLayout(stock_layout)

        discount_layout = QVBoxLayout()
        discount_layout.addWidget(QLabel("Действующая скидка (%):"))
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setStyleSheet(get_line_edit_style())
        self.discount_spin.setRange(0, 100)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setSuffix(" %")
        row_layout2.addLayout(discount_layout)

        form_layout.addLayout(row_layout2)

        form_layout.addStretch()
        form_container.setLayout(form_layout)
        scroll.setWidget(form_container)
        main_layout.addWidget(scroll, stretch=1)

        # ---- Кнопки ----
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.save_button = QPushButton("Сохранить")
        self.save_button.setStyleSheet(get_button_style(accent=True))
        self.save_button.clicked.connect(self._on_save)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setStyleSheet(get_button_style())
        self.cancel_button.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()

        # Кнопка удаления (только при редактировании)
        if self._is_editing:
            self.delete_button = QPushButton("Удалить товар")
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

    def _load_combo_data(self, combo, data_list):
        """Загружает данные в QComboBox."""
        combo.clear()
        for item in data_list:
            combo.addItem(item["name"], item["id"])

    def _load_product_data(self):
        """Загружает данные товара в форму."""
        product = get_product_by_id(self.product_id)
        if not product:
            QMessageBox.critical(
                self, "Ошибка",
                f"Товар с ID {self.product_id} не найден."
            )
            self._on_cancel()
            return

        self.id_label.setText(str(product["id"]))
        self.article_edit.setText(product.get("article", ""))
        self.name_edit.setText(product.get("name", ""))
        self.description_edit.setText(product.get("description", "") or "")
        self.unit_edit.setText(product.get("unit", "шт."))
        self.price_spin.setValue(float(product.get("price", 0)))
        self.stock_spin.setValue(int(product.get("stock_quantity", 0)))
        self.discount_spin.setValue(float(product.get("discount", 0)))

        # Категория
        cat_id = product.get("category_id")
        if cat_id:
            idx = self.category_combo.findData(cat_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)  # fallback — None

        # Производитель
        man_id = product.get("manufacturer_id")
        if man_id:
            idx = self.manufacturer_combo.findData(man_id)
            if idx >= 0:
                self.manufacturer_combo.setCurrentIndex(idx)

        # Поставщик
        sup_id = product.get("supplier_id")
        if sup_id:
            idx = self.supplier_combo.findData(sup_id)
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)

        # Фото
        img = product.get("image_path")
        if img:
            img_path = os.path.join(PRODUCTS_IMG_DIR, img)
            if os.path.exists(img_path):
                self.current_image_path = img_path
                self._show_photo_preview(img_path)
            else:
                self.current_image_path = None

    def _show_photo_preview(self, filepath):
        """Показывает предварительный просмотр фото."""
        if filepath and os.path.exists(filepath):
            pixmap = QPixmap(filepath)
            scaled = pixmap.scaled(
                MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.photo_preview.setPixmap(scaled)
            self.photo_preview.setText("")

    def _load_photo(self):
        """Загрузка фото из файла."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not filepath:
            return

        try:
            # Проверяем и масштабируем изображение
            img = Image.open(filepath)
            img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)

            # Сохраняем во временный путь до сохранения формы
            temp_dir = PRODUCTS_IMG_DIR
            os.makedirs(temp_dir, exist_ok=True)
            ext = os.path.splitext(filepath)[1].lower()
            if ext not in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
                ext = '.jpg'

            # Генерируем имя на основе артикула или timestamp
            article = self.article_edit.text().strip()
            if not article:
                import time
                article = f"temp_{int(time.time())}"

            dest_filename = f"{article}{ext}"
            dest_path = os.path.join(temp_dir, dest_filename)

            # Сохраняем масштабированное изображение
            img.save(dest_path, quality=85)
            self.current_image_path = dest_path
            self._show_photo_preview(dest_path)

        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка",
                f"Не удалось загрузить изображение:\n{e}"
            )

    def _clear_photo(self):
        """Удаляет текущее фото."""
        self.photo_preview.setPixmap(QPixmap())
        self.photo_preview.setText("Нет изображения")
        self.current_image_path = None

    def _validate(self):
        """
        Проверяет корректность введённых данных.
        Возвращает True, если данные валидны.
        """
        errors = []

        if not self.article_edit.text().strip():
            errors.append("Артикул товара не может быть пустым.")

        if not self.name_edit.text().strip():
            errors.append("Наименование товара не может быть пустым.")

        if self.category_combo.currentData() is None:
            errors.append("Выберите категорию товара.")

        if self.price_spin.value() < 0:
            errors.append("Цена не может быть отрицательной.")

        if self.stock_spin.value() < 0:
            errors.append("Количество на складе не может быть отрицательным.")

        if self.discount_spin.value() < 0:
            errors.append("Скидка не может быть отрицательной.")

        if self.discount_spin.value() > 100:
            errors.append("Скидка не может превышать 100%.")

        if errors:
            QMessageBox.warning(
                self, "Ошибка валидации",
                "Пожалуйста, исправьте следующие ошибки:\n\n" + "\n".join(errors)
            )
            return False

        return True

    def _on_save(self):
        """Сохранение товара."""
        if not self._validate():
            return

        article = self.article_edit.text().strip()
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        unit = self.unit_edit.text().strip() or "шт."
        price = self.price_spin.value()
        stock = self.stock_spin.value()
        discount = self.discount_spin.value()
        category_id = self.category_combo.currentData()
        manufacturer_id = self.manufacturer_combo.currentData()
        supplier_id = self.supplier_combo.currentData()

        # Обработка новых значений в комбобоксах (если введено вручную)
        if manufacturer_id is None:
            man_name = self.manufacturer_combo.currentText().strip()
            if man_name:
                manufacturer_id = self._get_or_create_ref("manufacturers", man_name)

        if supplier_id is None:
            sup_name = self.supplier_combo.currentText().strip()
            if sup_name:
                supplier_id = self._get_or_create_ref("suppliers", sup_name)

        # Путь к изображению
        image_path = None
        if self.current_image_path:
            image_path = os.path.basename(self.current_image_path)

        data = {
            "article": article,
            "name": name,
            "unit": unit,
            "price": price,
            "supplier_id": supplier_id,
            "manufacturer_id": manufacturer_id,
            "category_id": category_id,
            "discount": discount,
            "stock_quantity": stock,
            "description": description,
            "image_path": image_path,
        }

        try:
            if self._is_editing:
                update_product(self.product_id, data)
                msg = "Товар успешно обновлён."
            else:
                new_id = add_product(data)
                msg = f"Товар успешно добавлен (ID: {new_id})."

            QMessageBox.information(self, "Сохранение", msg)
            if self.on_save:
                self.on_save()

        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка сохранения",
                f"Не удалось сохранить товар:\n{e}"
            )

    def _get_or_create_ref(self, table, name):
        """Создаёт новую запись в справочнике и возвращает ID."""
        from database import create_connection
        conn = create_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT id FROM {table} WHERE name = %s", (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            cursor.execute(f"INSERT INTO {table} (name) VALUES (%s)", (name,))
            conn.commit()
            return cursor.lastrowid
        except:
            return None
        finally:
            cursor.close()
            conn.close()

    def _on_delete(self):
        """Удаление товара (только админ)."""
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить товар "
            f"'{self.name_edit.text().strip()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            result = delete_product(self.product_id)
            if result:
                QMessageBox.information(self, "Удаление", "Товар успешно удалён.")
                if self.on_save:
                    self.on_save()
            else:
                QMessageBox.warning(
                    self, "Невозможно удалить",
                    "Товар присутствует в одном или нескольких заказах.\n"
                    "Сначала удалите заказы с этим товаром."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка удаления",
                f"Не удалось удалить товар:\n{e}"
            )

    def _on_cancel(self):
        """Отмена и возврат к списку товаров."""
        if self.on_cancel:
            self.on_cancel()
