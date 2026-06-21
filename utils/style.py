"""
Общие стили и константы для приложения.
Цветовая схема и шрифты в соответствии с руководством по стилю.

См. книгу "Python 3 и PyQt 6":
  - QLabel — гл. 22, разд. "Надпись"
  - QPushButton — гл. 22, разд. "Кнопка"
  - QLineEdit — гл. 22, разд. "Поле ввода"
"""

# Цветовая схема
COLOR_MAIN = "#FFFFFF"      # Основной фон (белый)
COLOR_ACCENT = "#1B5E20"     # Тёмно-зелёный для панелей и заголовков
COLOR_ACCENT_LIGHT = "#E8F5E9"  # Светло-зелёный для фона
COLOR_ACTION = "#2E7D32"     # Зелёный для кнопок действий
COLOR_ACTION_HOVER = "#1B5E20"  # Тёмно-зелёный при наведении
COLOR_DISCOUNT_HIGH = "#2E8B57"  # Скидка > 15%
COLOR_OUT_OF_STOCK = "#E3F2FD"   # Нет на складе (светло-голубой)
COLOR_PRICE_CROSSED = "#D32F2F"  # Перечёркнутая цена (тёмно-красный)

# Шрифт
FONT_FAMILY = "Times New Roman"
FONT_SIZE_DEFAULT = 11
FONT_SIZE_TITLE = 16
FONT_SIZE_CARD_TITLE = 13
FONT_SIZE_SMALL = 9

# Общий стиль окна
# Цвет текста задан явно (#333333), чтобы избежать белого текста на белом фоне
WINDOW_STYLE = f"""
    QWidget {{
        font-family: "{FONT_FAMILY}";
        font-size: {FONT_SIZE_DEFAULT}pt;
        background-color: {COLOR_MAIN};
        color: #333333;
    }}
"""


def get_button_style(accent=False):
    """
    Возвращает стиль для кнопки.
    Если accent=True — цвет акцентирования.
    """
    if accent:
        bg = COLOR_ACTION
        hover_bg = COLOR_ACTION_HOVER
        text_color = "#E8F5E9"
    else:
        bg = "#E0E0E0"
        hover_bg = "#BDBDBD"
        text_color = "#000000"
    return f"""
        QPushButton {{
            font-family: "{FONT_FAMILY}";
            font-size: {FONT_SIZE_DEFAULT}pt;
            background-color: {bg};
            color: {text_color};
            border: 1px solid #999999;
            border-radius: 6px;
            padding: 8px 20px;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            border-color: #666666;
        }}
        QPushButton:pressed {{
            background-color: #555555;
        }}
    """


def get_line_edit_style():
    """Стиль для полей ввода."""
    return f"""
        QLineEdit {{
            font-family: "{FONT_FAMILY}";
            font-size: {FONT_SIZE_DEFAULT}pt;
            border: 1px solid #BDBDBD;
            border-radius: 4px;
            padding: 6px 10px;
            background-color: {COLOR_MAIN};
        }}
        QLineEdit:focus {{
            border-color: {COLOR_ACTION};
            border-width: 2px;
        }}
    """


def get_combo_box_style():
    """Стиль для выпадающих списков."""
    return f"""
        QComboBox {{
            font-family: "{FONT_FAMILY}";
            font-size: {FONT_SIZE_DEFAULT}pt;
            border: 1px solid #BDBDBD;
            border-radius: 4px;
            padding: 6px 10px;
            background-color: {COLOR_MAIN};
        }}
        QComboBox:focus {{
            border-color: {COLOR_ACTION};
            border-width: 2px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
    """


def get_card_frame_style(has_discount=False, out_of_stock=False):
    """
    Стиль рамки карточки товара.
    has_discount — скидка > 15%
    out_of_stock — товара нет на складе
    """
    bg = COLOR_MAIN
    if has_discount:
        bg = COLOR_DISCOUNT_HIGH
    elif out_of_stock:
        bg = COLOR_OUT_OF_STOCK

    return f"""
        QFrame {{
            background-color: {bg};
            border: 2px solid #CCCCCC;
            border-radius: 8px;
            padding: 10px;
        }}
        QFrame:hover {{
            border-color: #999999;
        }}
    """


def get_label_style(bold=False, color=None, size=None):
    """Стиль для QLabel."""
    parts = [f'font-family: "{FONT_FAMILY}";']
    if bold:
        parts.append("font-weight: bold;")
    if color:
        parts.append(f"color: {color};")
    if size:
        parts.append(f"font-size: {size}pt;")
    else:
        parts.append(f"font-size: {FONT_SIZE_DEFAULT}pt;")
    return "QLabel {" + " ".join(parts) + "}"
