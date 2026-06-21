"""
Окно авторизации пользователя.

Позволяет:
  - Войти по логину и паролю из таблицы users.
  - Войти как гость (без авторизации).

После входа открывается окно списка товаров с правами,
соответствующими роли пользователя.

Ссылки на книгу "Python 3 и PyQt 6":
  - QLabel — гл. 22, разд. "Надпись"
  - QLineEdit — гл. 22, разд. "Поле ввода"
  - QPushButton — гл. 22, разд. "Кнопка"
  - QMessageBox — гл. 27, разд. "QMessageBox"
  - Окна PyQt6 — гл. 18–19
  - Сигналы и события — гл. 20
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt

from database import create_connection
from utils.style import (
    COLOR_MAIN, COLOR_ACCENT, FONT_FAMILY, FONT_SIZE_TITLE, FONT_SIZE_DEFAULT,
    get_button_style, get_line_edit_style
)


class LoginWindow(QWidget):
    """
    Окно входа в систему.
    После успешной авторизации испускает сигнал login_success(user_data).
    """

    def __init__(self, on_login_success):
        """
        on_login_success — функция обратного вызова, принимающая
        dict с данными пользователя (или None для гостя).
        """
        super().__init__()
        self.on_login_success = on_login_success
        self._setup_ui()

    def _setup_ui(self):
        """Настройка интерфейса окна авторизации."""
        self.setWindowTitle("Авторизация — ООО «Обувь»")
        self.setGeometry(300, 300, 450, 500)
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_MAIN}; color: #333333; }}")

        # Главный вертикальный layout
        main_vbox = QVBoxLayout()
        main_vbox.setSpacing(0)
        main_vbox.setContentsMargins(0, 0, 0, 0)

        # Шапка с тёмно-зелёным фоном
        header_widget = QWidget()
        header_widget.setFixedHeight(200)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_ACCENT};
            }}
        """)
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(20, 10, 20, 10)

        # Логотип
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources", "Icon.png"
        )
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(
                80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(logo_label)

        # Заголовок
        title_label = QLabel("ООО «Обувь»")
        title_label.setFont(QFont(FONT_FAMILY, 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #E8F5E9; background: transparent;")
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Вход в информационную систему")
        subtitle_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #C8E6C9; background: transparent;")
        header_layout.addWidget(subtitle_label)

        header_widget.setLayout(header_layout)
        main_vbox.addWidget(header_widget)

        # Форма входа (белая область, растягивается на всю высоту)
        form_widget = QWidget()
        form_widget.setStyleSheet(f"QWidget#formWidget {{ background-color: {COLOR_MAIN}; }}")
        form_widget.setObjectName("formWidget")
        form_layout = QVBoxLayout()
        form_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(50, 20, 50, 20)

        # Поле логина
        login_label = QLabel("Логин:")
        login_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        login_label.setStyleSheet("color: #000000; background: transparent;")
        form_layout.addWidget(login_label)

        self.login_edit = QLineEdit()
        self.login_edit.setObjectName("LineEditLogin")  # Для тестирования
        self.login_edit.setPlaceholderText("Введите логин")
        self.login_edit.setStyleSheet(get_line_edit_style())
        form_layout.addWidget(self.login_edit)

        # Поле пароля
        password_label = QLabel("Пароль:")
        password_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEFAULT))
        password_label.setStyleSheet("color: #000000; background: transparent;")
        form_layout.addWidget(password_label)

        self.password_edit = QLineEdit()
        self.password_edit.setObjectName("LineEditPassword")  # Для тестирования
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setStyleSheet(get_line_edit_style())
        form_layout.addWidget(self.password_edit)

        # Обработка Enter в полях ввода
        self.password_edit.returnPressed.connect(self._on_login_clicked)

        form_layout.addSpacing(10)

        # Кнопка "Войти"
        self.login_button = QPushButton("Войти")
        self.login_button.setStyleSheet(get_button_style(accent=True))
        self.login_button.clicked.connect(self._on_login_clicked)
        form_layout.addWidget(self.login_button)

        # Кнопка "Войти как гость"
        self.guest_button = QPushButton("Войти как гость")
        self.guest_button.setStyleSheet(get_button_style())
        self.guest_button.clicked.connect(self._on_guest_clicked)
        form_layout.addWidget(self.guest_button)

        # Информация о ролях (только для разработки)
        info_label = QLabel(
            "Роли в системе:\n"
            "• Администратор — полный доступ\n"
            "• Менеджер — товары (поиск/фильтр) и заказы\n"
            "• Авторизованный клиент — просмотр товаров\n"
            "• Гость — просмотр товаров без поиска"
        )
        info_label.setFont(QFont(FONT_FAMILY, 8))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #9E9E9E;")
        form_layout.addWidget(info_label)

        form_widget.setLayout(form_layout)
        main_vbox.addWidget(form_widget, stretch=1)

        self.setLayout(main_vbox)

    def _on_login_clicked(self):
        """Обработка нажатия кнопки «Войти»."""
        login = self.login_edit.text().strip()
        password = self.password_edit.text().strip()

        if not login or not password:
            QMessageBox.warning(
                self, "Предупреждение",
                "Пожалуйста, заполните все поля для входа."
            )
            return

        connection = create_connection()
        if not connection:
            QMessageBox.critical(
                self, "Ошибка",
                "Не удалось подключиться к базе данных.\n"
                "Проверьте, запущен ли сервер MySQL."
            )
            return

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT u.id, u.full_name, u.role_id, r.name AS role_name "
                "FROM users u "
                "JOIN roles r ON u.role_id = r.id "
                "WHERE u.login = %s AND u.password = %s",
                (login, password)
            )
            user = cursor.fetchone()
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"Ошибка при авторизации:\n{e}"
            )
            user = None
        finally:
            cursor.close()
            connection.close()

        if user:
            self.on_login_success(user)
        else:
            QMessageBox.warning(
                self, "Ошибка входа",
                "Неверный логин или пароль.\n"
                "Проверьте правильность введённых данных."
            )

    def _on_guest_clicked(self):
        """Вход как гость (без авторизации)."""
        guest_data = {
            "id": None,
            "full_name": "Гость",
            "role_id": 0,  # специальная роль
            "role_name": "Гость"
        }
        self.on_login_success(guest_data)
