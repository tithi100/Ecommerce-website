from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from datetime import datetime

ADMIN_REGISTRATION_KEY = "qwerty003"  # Change this to a secure key
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "983105R!"
DEFAULT_ADMIN_EMAIL = "admin@example.com"

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    # Create users table with user_type
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            user_type TEXT DEFAULT 'customer'
        )
    ''')
    conn.commit()  # Commit the table creation
    
    # Create products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            stock INTEGER NOT NULL
        )
    ''')
    conn.commit()  # Commit the table creation
    
    # Create seller_products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS seller_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            stock INTEGER NOT NULL,
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')
    conn.commit()  # Commit the table creation
    
    # Create orders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()  # Commit the table creation
    
    # Create order_items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_at_time REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    conn.commit()  # Commit the table creation
    
    # Now check for admin user and create if doesn't exist
    c.execute('SELECT COUNT(*) FROM users WHERE user_type = "admin"')
    if c.fetchone()[0] == 0:
        # Create default admin user
        admin_password = generate_password_hash(DEFAULT_ADMIN_PASSWORD)
        try:
            c.execute('''
                INSERT INTO users (username, password, email, user_type)
                VALUES (?, ?, ?, 'admin')
            ''', (DEFAULT_ADMIN_USERNAME, admin_password, DEFAULT_ADMIN_EMAIL))
            print("Default admin user created successfully")
        except sqlite3.IntegrityError:
            print("Default admin user already exists")
    
    # Add sample products if none exist
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO products (name, price, description, stock)
            VALUES 
            ('Laptop', 999.99, 'High-performance laptop', 10),
            ('Smartphone', 499.99, 'Latest model smartphone', 15),
            ('Headphones', 79.99, 'Wireless headphones', 20)
        ''')
    
    conn.commit()
    conn.close()

def get_cart():
    return session.get('cart', {})

def update_cart(product_id, quantity):
    cart = get_cart()
    if quantity <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = quantity
    session['cart'] = cart

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    # Get products with explicit type casting for price
    c.execute('SELECT id, name, CAST(price AS FLOAT) as price, description, stock FROM products')
    regular_products = c.fetchall()
    
    c.execute('SELECT id, name, CAST(price AS FLOAT) as price, description, stock FROM seller_products')
    seller_products = c.fetchall()
    
    conn.close()
    
    # Convert to list of tuples with proper types
    all_products = [
        (
            int(p[0]),
            str(p[1]),
            float(p[2]),
            str(p[3]),
            int(p[4])
        ) 
        for p in (regular_products + seller_products)
    ]
    
    return render_template('home.html', products=all_products)


@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if session.get('user_type') != 'seller':
        flash('Access denied. Seller account required.')
        return redirect(url_for('home'))
    
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('SELECT * FROM seller_products WHERE seller_id = ?', (session['user_id'],))
    products = c.fetchall()
    conn.close()
    return render_template('seller_dashboard.html', products=products)

@app.route('/seller/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if session.get('user_type') != 'seller':
        flash('Access denied. Seller account required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO seller_products (seller_id, name, price, description, stock)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], name, price, description, stock))
        conn.commit()
        conn.close()
        
        flash('Product added successfully!')
        return redirect(url_for('seller_dashboard'))
        
    return render_template('add_product.html')

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    cart = get_cart()
    product_id_str = str(product_id)
    if product_id_str in cart:
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1
    session['cart'] = cart
    flash('Product added to cart!')
    return redirect(url_for('home'))

@app.route('/cart')
@login_required
def view_cart():
    cart = get_cart()
    if not cart:
        return render_template('cart.html', cart_items=[])
    
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        # Check regular products
        c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = c.fetchone()
        
        if not product:
            # Check seller products
            c.execute('SELECT * FROM seller_products WHERE id = ?', (product_id,))
            product = c.fetchone()
        
        if product:
            item_total = product[2] * quantity
            total += item_total
            cart_items.append({
                'id': product[0],
                'name': product[1],
                'price': product[2],
                'quantity': quantity,
                'item_total': item_total
            })
    
    conn.close()
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart', methods=['POST'])
@login_required
def update_cart_quantity():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 0))
    update_cart(product_id, quantity)
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        cart = get_cart()
        if not cart:
            flash('Your cart is empty!')
            return redirect(url_for('view_cart'))
        
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO orders (user_id, status)
                VALUES (?, 'pending')
            ''', (session['user_id'],))
            order_id = c.lastrowid
            
            for product_id, quantity in cart.items():
                # Check regular products
                c.execute('SELECT price, stock FROM products WHERE id = ?', (product_id,))
                product = c.fetchone()
                
                if not product:
                    # Check seller products
                    c.execute('SELECT price, stock FROM seller_products WHERE id = ?', (product_id,))
                    product = c.fetchone()
                
                if not product:
                    raise Exception(f'Product {product_id} not found')
                
                price, stock = product
                
                if stock < quantity:
                    raise Exception(f'Not enough stock for product ID {product_id}')
                
                c.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, product_id, quantity, price))
                
                # Update stock
                c.execute('''
                    UPDATE products 
                    SET stock = stock - ? 
                    WHERE id = ?
                ''', (quantity, product_id))
            
            conn.commit()
            session.pop('cart', None)
            flash('Order placed successfully!')
            return redirect(url_for('home'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error processing order: {str(e)}')
            return redirect(url_for('view_cart'))
        
        finally:
            conn.close()
    
    return render_template('checkout.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user_type = request.form.get('user_type', 'customer')
        
        # Validate admin registration
        if user_type == 'admin':
            admin_key = request.form.get('admin_key', '')
            if admin_key != ADMIN_REGISTRATION_KEY:
                flash('Invalid admin registration key!')
                return redirect(url_for('signup'))
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO users (username, password, email, user_type)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_password, email, user_type))
            conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!')
        finally:
            conn.close()
            
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['user_type'] = user[4]
            flash('Logged in successfully!')
            
            # Redirect based on user type
            if user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user[4] == 'seller':
                return redirect(url_for('seller_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid username or password!')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('user_type', None)
    session.pop('cart', None)
    flash('Logged out successfully!')
    return redirect(url_for('home'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# Add these new routes after the existing routes

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    # Get all users except current admin
    c.execute('''
        SELECT id, username, email, user_type 
        FROM users 
        WHERE id != ?
        ORDER BY user_type, username
    ''', (session['user_id'],))
    users = c.fetchall()
    
    # Get all products (both regular and seller products)
    c.execute('''
        SELECT 'regular' as source, id, name, price, stock, description
        FROM products
        UNION ALL
        SELECT 'seller' as source, id, name, price, stock, description
        FROM seller_products
    ''')
    products = c.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', users=users, products=products)

@app.route('/admin/remove_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def remove_user(user_id):
    if user_id == session['user_id']:
        flash('Cannot remove your own admin account!')
        return redirect(url_for('admin_dashboard'))
    
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    try:
        # First, remove all seller products if user is a seller
        c.execute('DELETE FROM seller_products WHERE seller_id = ?', (user_id,))
        
        # Remove user's orders and order items
        c.execute('SELECT id FROM orders WHERE user_id = ?', (user_id,))
        order_ids = [row[0] for row in c.fetchall()]
        
        for order_id in order_ids:
            c.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
        
        c.execute('DELETE FROM orders WHERE user_id = ?', (user_id,))
        
        # Finally, remove the user
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        flash('User and all associated data removed successfully!')
        
    except sqlite3.Error as e:
        conn.rollback()
        flash(f'Error removing user: {str(e)}')
    
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove_product', methods=['POST'])
@login_required
@admin_required
def remove_product():
    product_id = request.form.get('product_id')
    product_source = request.form.get('product_source')
    
    if not product_id or not product_source:
        flash('Invalid request!')
        return redirect(url_for('admin_dashboard'))
    
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    try:
        # Remove order items containing this product
        c.execute('DELETE FROM order_items WHERE product_id = ?', (product_id,))
        
        # Remove the product from the appropriate table
        if product_source == 'regular':
            c.execute('DELETE FROM products WHERE id = ?', (product_id,))
        else:
            c.execute('DELETE FROM seller_products WHERE id = ?', (product_id,))
        
        conn.commit()
        flash('Product removed successfully!')
        
    except sqlite3.Error as e:
        conn.rollback()
        flash(f'Error removing product: {str(e)}')
    
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)