"""
Вспомогательные функции для работы с базой данных.
Инкапсулируют типовые запросы к БД.

См. книгу "Python 3 и PyQt 6" гл. 24 (работа с базами данных).
"""

from database import create_connection


def get_user_by_login(login, password):
    """
    Проверяет логин и пароль пользователя.
    Возвращает dict с данными пользователя или None.
    """
    connection = create_connection()
    if not connection:
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT u.id, u.full_name, u.role_id, r.name AS role_name "
            "FROM users u "
            "JOIN roles r ON u.role_id = r.id "
            "WHERE u.login = %s AND u.password = %s",
            (login, password)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def get_all_products():
    """
    Возвращает список всех товаров со связанными данными.
    """
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                p.id, p.article, p.name, p.unit, p.price,
                p.discount, p.stock_quantity, p.description,
                p.image_path,
                c.name AS category_name,
                m.name AS manufacturer_name,
                s.name AS supplier_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            JOIN manufacturers m ON p.manufacturer_id = m.id
            JOIN suppliers s ON p.supplier_id = s.id
            ORDER BY p.name
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_filtered_products(search_text="", supplier_id=None, sort_order=""):
    """
    Возвращает товары с фильтрацией по поиску и поставщику,
    и сортировкой по количеству на складе.

    search_text — поиск по артикулу, наименованию, категории,
                  описанию, производителю, поставщику, единице измерения.
    supplier_id — ID поставщика для фильтрации (None = все).
    sort_order — "asc" / "desc" по stock_quantity, "" — без сортировки.
    """
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT
                p.id, p.article, p.name, p.unit, p.price,
                p.discount, p.stock_quantity, p.description,
                p.image_path,
                c.name AS category_name,
                m.name AS manufacturer_name,
                s.name AS supplier_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            JOIN manufacturers m ON p.manufacturer_id = m.id
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE 1=1
        """
        params = []

        if search_text:
            query += """
                AND (p.article LIKE %s
                     OR p.name LIKE %s
                     OR c.name LIKE %s
                     OR p.description LIKE %s
                     OR m.name LIKE %s
                     OR s.name LIKE %s
                     OR p.unit LIKE %s)
            """
            like = f"%{search_text}%"
            params.extend([like] * 7)

        if supplier_id:
            query += " AND p.supplier_id = %s"
            params.append(supplier_id)

        if sort_order == "asc":
            query += " ORDER BY p.stock_quantity ASC"
        elif sort_order == "desc":
            query += " ORDER BY p.stock_quantity DESC"
        else:
            query += " ORDER BY p.name"

        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_product_by_id(product_id):
    """
    Возвращает один товар по его ID.
    """
    connection = create_connection()
    if not connection:
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                p.id, p.article, p.name, p.unit, p.price,
                p.discount, p.stock_quantity, p.description,
                p.image_path, p.category_id, p.supplier_id, p.manufacturer_id,
                c.name AS category_name,
                m.name AS manufacturer_name,
                s.name AS supplier_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            JOIN manufacturers m ON p.manufacturer_id = m.id
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = %s
        """, (product_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def add_product(data):
    """
    Добавляет новый товар.
    data — dict с ключами: article, name, unit, price, supplier_id,
           manufacturer_id, category_id, discount, stock_quantity,
           description, image_path.
    Возвращает ID нового товара или None при ошибке.
    """
    connection = create_connection()
    if not connection:
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO products
            (article, name, unit, price, supplier_id, manufacturer_id,
             category_id, discount, stock_quantity, description, image_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["article"], data["name"], data["unit"], data["price"],
            data["supplier_id"], data["manufacturer_id"], data["category_id"],
            data["discount"], data["stock_quantity"], data["description"],
            data["image_path"]
        ))
        connection.commit()
        return cursor.lastrowid
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def update_product(product_id, data):
    """
    Обновляет данные товара.
    """
    connection = create_connection()
    if not connection:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE products SET
                article = %s, name = %s, unit = %s, price = %s,
                supplier_id = %s, manufacturer_id = %s, category_id = %s,
                discount = %s, stock_quantity = %s, description = %s,
                image_path = %s
            WHERE id = %s
        """, (
            data["article"], data["name"], data["unit"], data["price"],
            data["supplier_id"], data["manufacturer_id"], data["category_id"],
            data["discount"], data["stock_quantity"], data["description"],
            data["image_path"], product_id
        ))
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def delete_product(product_id):
    """
    Удаляет товар, если он не присутствует ни в одном заказе.
    Возвращает True при успехе, False если товар есть в заказе.
    """
    connection = create_connection()
    if not connection:
        return False
    cursor = connection.cursor()
    try:
        # Проверяем, есть ли товар в заказах
        cursor.execute(
            "SELECT COUNT(*) FROM order_items WHERE product_id = %s",
            (product_id,)
        )
        count = cursor.fetchone()[0]
        if count > 0:
            return False

        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def get_all_categories():
    """Возвращает список всех категорий."""
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_all_manufacturers():
    """Возвращает список всех производителей."""
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM manufacturers ORDER BY name")
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_all_suppliers():
    """Возвращает список всех поставщиков."""
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM suppliers ORDER BY name")
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_all_clients():
    """Возвращает список всех клиентов (роль = 3)."""
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, full_name FROM users WHERE role_id = 3 ORDER BY full_name"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_all_pickup_points():
    """Возвращает список всех пунктов выдачи."""
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, address FROM pickup_points ORDER BY address")
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_all_order_statuses():
    """Возвращает список всех статусов заказов."""
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM order_statuses ORDER BY id")
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_all_orders():
    """
    Возвращает список заказов с расшифровками.
    """
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                o.id, o.order_date, o.delivery_date, o.receive_code,
                pp.address AS pickup_address,
                u.full_name AS client_name,
                os.name AS status_name,
                (SELECT GROUP_CONCAT(CONCAT(p2.article, ' (', oi2.quantity, ')')
                 SEPARATOR ', ')
                 FROM order_items oi2
                 JOIN products p2 ON oi2.product_id = p2.id
                 WHERE oi2.order_id = o.id) AS items_info
            FROM orders o
            JOIN pickup_points pp ON o.pickup_point_id = pp.id
            JOIN users u ON o.client_id = u.id
            JOIN order_statuses os ON o.status_id = os.id
            ORDER BY o.order_date DESC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_order_by_id(order_id):
    """
    Возвращает один заказ с составом.
    """
    connection = create_connection()
    if not connection:
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                o.id, o.order_date, o.delivery_date, o.receive_code,
                o.pickup_point_id, o.client_id, o.status_id,
                pp.address AS pickup_address,
                u.full_name AS client_name,
                os.name AS status_name
            FROM orders o
            JOIN pickup_points pp ON o.pickup_point_id = pp.id
            JOIN users u ON o.client_id = u.id
            JOIN order_statuses os ON o.status_id = os.id
            WHERE o.id = %s
        """, (order_id,))
        order = cursor.fetchone()
        if not order:
            return None

        # Получаем состав заказа
        cursor.execute("""
            SELECT oi.product_id, oi.quantity, p.article, p.name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,))
        order["items"] = cursor.fetchall()
        return order
    finally:
        cursor.close()
        connection.close()


def add_order(data):
    """
    Добавляет новый заказ.
    data — dict с order_date, delivery_date, pickup_point_id,
           client_id, receive_code, status_id, items (список товаров).
    """
    connection = create_connection()
    if not connection:
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO orders
            (order_date, delivery_date, pickup_point_id,
             client_id, receive_code, status_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data["order_date"], data.get("delivery_date"),
            data["pickup_point_id"], data["client_id"],
            data.get("receive_code", ""), data["status_id"]
        ))
        order_id = cursor.lastrowid

        # Добавляем товары
        for item in data.get("items", []):
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (order_id, item["product_id"], item["quantity"]))

        connection.commit()
        return order_id
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def update_order(order_id, data):
    """
    Обновляет заказ.
    """
    connection = create_connection()
    if not connection:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE orders SET
                order_date = %s, delivery_date = %s,
                pickup_point_id = %s, client_id = %s,
                receive_code = %s, status_id = %s
            WHERE id = %s
        """, (
            data["order_date"], data.get("delivery_date"),
            data["pickup_point_id"], data["client_id"],
            data.get("receive_code", ""), data["status_id"],
            order_id
        ))

        # Удаляем старые товары и добавляем новые
        cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
        for item in data.get("items", []):
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (order_id, item["product_id"], item["quantity"]))

        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def delete_order(order_id):
    """
    Удаляет заказ и его состав (CASCADE).
    """
    connection = create_connection()
    if not connection:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()
