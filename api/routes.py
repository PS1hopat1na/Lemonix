from flask import Blueprint, render_template, request, redirect, session, flash, url_for, jsonify
import pg8000.native
import urllib.parse
import os
from datetime import datetime

bp = Blueprint('main', __name__)

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres.wsmvmimkbigkwzigivxz:89950510391z@aws-0-eu-central-1.pooler.supabase.com:6543/postgres")

def get_db_connection():
    result = urllib.parse.urlparse(DATABASE_URL)
    username = result.username
    password = urllib.parse.unquote(result.password) if result.password else ""
    database = result.path[1:]
    hostname = result.hostname
    port = result.port

    conn = pg8000.native.Connection(
        user=username,
        password=password,
        database=database,
        host=hostname,
        port=port
    )
    return conn

def fetchall_dict(rows, description):
    columns = [desc[0] for desc in description]
    return [dict(zip(columns, row)) for row in rows]

def get_all_products():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY id DESC")
    products = fetchall_dict(rows, conn.description)
    conn.close()
    return products

def get_cart_count(phone):
    if not phone:
        return 0
    conn = get_db_connection()
    rows = conn.execute("SELECT COUNT(*) FROM carts WHERE user_phone = %s", (phone,))
    count = rows[0][0] if rows else 0
    conn.close()
    return count

@bp.app_context_processor
def inject_cart_count():
    phone = session.get('phone')
    return dict(cart_count=get_cart_count(phone))

@bp.route('/')
def index():
    phone = session.get('phone')
    is_admin = session.get('is_admin', False)
    return render_template('index.html', phone=phone, is_admin=is_admin)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        username = request.form['username']
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM users WHERE phone = %s", (phone,))
        user_row = rows[0] if rows else None
        user = None
        if user_row:
            user = dict(zip([desc[0] for desc in conn.description], user_row))
        if not user:
            inserted_rows = conn.execute("INSERT INTO users (phone, username) VALUES (%s, %s) RETURNING *", (phone, username))
            inserted_row = inserted_rows[0]
            user = dict(zip([desc[0] for desc in conn.description], inserted_row))
            conn.commit()
        else:
            if username and user.get('username') != username:
                conn.execute("UPDATE users SET username=%s WHERE phone=%s", (username, phone))
                conn.commit()
        conn.close()
        session['phone'] = phone
        session['username'] = user.get('username') or username
        session['is_admin'] = user.get('is_admin', False)
        return redirect(url_for('main.index'))
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.pop('phone', None)
    session.pop('is_admin', None)
    session.pop('username', None)
    return redirect(url_for('main.index'))

@bp.route('/shop')
def shop():
    products = get_all_products()
    phone = session.get('phone')
    is_admin = session.get('is_admin', False)
    return render_template('shop.html', products=products, phone=phone, is_admin=is_admin)

@bp.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    phone = session.get('phone')
    is_admin = session.get('is_admin', False)
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product_row = rows[0] if rows else None
    product = dict(zip([desc[0] for desc in conn.description], product_row)) if product_row else None

    review_rows = conn.execute("SELECT * FROM reviews WHERE product_id = %s ORDER BY created_at DESC", (product_id,))
    reviews = fetchall_dict(review_rows, conn.description)

    avg_rating_rows = conn.execute("SELECT AVG(rating) FROM reviews WHERE product_id = %s", (product_id,))
    avg_rating_row = avg_rating_rows[0] if avg_rating_rows else None
    avg_rating = avg_rating_row[0] if avg_rating_row else 0

    rec_rows = conn.execute("SELECT * FROM products WHERE id != %s ORDER BY RANDOM() LIMIT 4", (product_id,))
    recommendations = fetchall_dict(rec_rows, conn.description)

    conn.close()

    if request.method == 'POST' and phone:
        rating = int(request.form['rating'])
        text = request.form['text']
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO reviews (product_id, user_phone, rating, text) VALUES (%s, %s, %s, %s)",
            (product_id, phone, rating, text)
        )
        conn.commit()
        conn.close()
        flash('Ваш отзыв добавлен!')
        return redirect(url_for('main.product_detail', product_id=product_id))

    return render_template(
        'product.html',
        product=product,
        reviews=reviews,
        avg_rating=round(avg_rating, 1),
        phone=phone,
        is_admin=is_admin,
        recommendations=recommendations
    )

@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    phone = session.get('phone')
    if not phone:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Требуется вход'}), 403
        flash('Войдите, чтобы добавить в корзину!')
        return redirect(url_for('main.login'))
    conn = get_db_connection()
    conn.execute("INSERT INTO carts (user_phone, product_id) VALUES (%s, %s)", (phone, product_id))
    conn.commit()
    conn.close()
    count = get_cart_count(phone)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'count': count, 'success': True})
    flash('Товар добавлен в корзину!')
    return redirect(url_for('main.cart'))

@bp.route('/cart', methods=['GET'])
def cart():
    phone = session.get('phone')
    if not phone:
        flash('Войдите, чтобы видеть корзину!')
        return redirect(url_for('main.login'))
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT c.id as cart_id, p.* FROM carts c JOIN products p ON c.product_id=p.id WHERE c.user_phone=%s", (phone,))
    cart_items = fetchall_dict(rows, conn.description)
    cart_total = sum(item['price'] for item in cart_items)
    order_id = 100000 + int(datetime.now().timestamp()) % 100000
    order_date = datetime.now().strftime('%d.%m.%Y %H:%M')
    conn.close()
    return render_template('cart.html', cart_items=cart_items, phone=phone, cart_total=cart_total, order_id=order_id, order_date=order_date)

@bp.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    phone = session.get('phone')
    if not phone:
        return jsonify({'success': False, 'msg': 'Войдите в аккаунт'})
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM carts WHERE id=%s AND user_phone=%s", (cart_id, phone))
        conn.commit()
        rows = conn.execute("""
            SELECT c.id, p.name, p.price, p.image_url
            FROM carts c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_phone = %s
        """, (phone,))
        rows_data = fetchall_dict(rows, conn.description)
        cart_total = sum(row['price'] for row in rows_data)
        cart_count = len(rows_data)
        session['cart_count'] = cart_count
        return jsonify({'success': True, 'cart_total': cart_total, 'cart_count': cart_count})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'msg': str(e)})
    finally:
        conn.close()

@bp.route('/about')
def about():
    phone = session.get('phone')
    is_admin = session.get('is_admin', False)
    return render_template('about.html', phone=phone, is_admin=is_admin)

@bp.route('/policy')
def policy():
    phone = session.get('phone')
    is_admin = session.get('is_admin', False)
    return render_template('policy.html', phone=phone, is_admin=is_admin)

@bp.route('/contact')
def contact():
    phone = session.get('phone')
    is_admin = session.get('is_admin', False)
    return render_template('contact.html', phone=phone, is_admin=is_admin)

@bp.route('/admin', methods=['GET', 'POST'])
def admin():
    phone = session.get('phone')
    is_admin = session.get('is_admin', False)
    if not is_admin:
        flash('Доступ только для администратора!')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_url = request.form['image_url']
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO products (name, description, price, image_url) VALUES (%s, %s, %s, %s)",
            (name, description, price, image_url)
        )
        conn.commit()
        conn.close()
        flash('Товар успешно добавлен!')
    products = get_all_products()
    return render_template('admin.html', phone=phone, is_admin=is_admin, products=products)

@bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('is_admin', False):
        flash('Нет доступа!')
        return redirect(url_for('main.index'))
    conn = get_db_connection()
    conn.execute("DELETE FROM reviews WHERE product_id = %s", (product_id,))
    conn.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    conn.close()
    flash('Товар удалён')
    return redirect(url_for('main.admin'))

@bp.route('/checkout', methods=['POST'])
def checkout():
    phone = session.get('phone')
    if not phone:
        return jsonify({'success': False, 'msg': 'Войдите в аккаунт'})
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT c.id, p.name, p.price
            FROM carts c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_phone = %s
        """, (phone,))
        items = fetchall_dict(rows, conn.description)
        if not items:
            return jsonify({'success': False, 'msg': 'Корзина пуста'})
        order_id = 100000 + int(datetime.now().timestamp()) % 100000
        total = sum(item['price'] for item in items)
        conn.execute("DELETE FROM carts WHERE user
