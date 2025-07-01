import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'sda_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# DB initialization
from werkzeug.security import generate_password_hash

def init_db():
    with sqlite3.connect('inventory.db') as conn:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            type TEXT NOT NULL,
            qty INTEGER DEFAULT 0,
            avg_buy_price REAL,
            photo TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS incoming (
            date TEXT, itemid INTEGER, item TEXT, type TEXT, qty INTEGER, buyprice REAL
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS outgoing (
            date TEXT, itemid INTEGER, item TEXT, type TEXT, qty INTEGER, sellprice REAL
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            name TEXT NOT NULL,
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            level TEXT CHECK(level IN ('Admin', 'Write', 'Read')) NOT NULL
        )''')
        # Insert default admin user if not exists
        cur.execute("SELECT * FROM users WHERE username = 'Admin'")
        if not cur.fetchone():
            hashed_pw = generate_password_hash('Bhaskar123')
            cur.execute("INSERT INTO users (name, username, password, level) VALUES (?, ?, ?, ?)",
                        ('Ramanuj', 'Admin', hashed_pw, 'Admin'))
        conn.commit()


# Initialize DB when app starts

# Routes
@app.route('/')
def login():
    return render_template('login.html')


@app.route('/do_login', methods=['POST'])
def do_login():
    user = request.form['username']
    pw = request.form['password']
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row  # ✅ Enables named column access
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (user,))
        row = cur.fetchone()

        if row and check_password_hash(row['password'], pw):  # ✅ Correct hash check
            session['logged_in'] = True
            session['username'] = row['username']
            session['fullname'] = row['name']  # ✅ Storing full name
            session['level'] = row['level']
            return redirect(url_for('dashboard'))

    return render_template('login.html', error="Invalid credentials")

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    return render_template('dashboard.html')

@app.route('/items')
def items():
    if not session.get('logged_in'):
        return redirect('/')

    q = request.args.get('q', '')
    item_type = request.args.get('type', '')

    with sqlite3.connect('inventory.db') as conn:
        cur = conn.cursor()
        
        # Get all unique types for the dropdown
        cur.execute("SELECT DISTINCT type FROM items")
        all_types = [row[0] for row in cur.fetchall()]

        # Build query based on filters
        query = "SELECT * FROM items WHERE 1=1"
        params = []
        if q:
            query += " AND item LIKE ?"
            params.append('%' + q + '%')
        if item_type:
            query += " AND type = ?"
            params.append(item_type)

        cur.execute(query, params)
        results = cur.fetchall()

    return render_template('items.html', items=results, query=q, selected_type=item_type, all_types=all_types)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if not session.get('logged_in'):
        return redirect('/')

    if request.method == 'POST':
        item = request.form['item']
        type_ = request.form['type']
        qty = int(request.form['qty'])
        price = float(request.form['price'])
        photo = request.files['photo']

        with sqlite3.connect('inventory.db') as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO items (item, type, qty, avg_buy_price) VALUES (?, ?, ?, ?)",
                        (item, type_, qty, price))
            item_id = cur.lastrowid

            if photo and photo.filename != '':
                ext = os.path.splitext(photo.filename)[1]
                filename = f"{item_id}{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(filepath)

                cur.execute("UPDATE items SET photo = ? WHERE id = ?", (filename, item_id))

            conn.commit()

        return redirect(url_for('items'))

    return render_template('add_item.html', item=None)

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if not session.get('logged_in'):
        return redirect('/')

    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if request.method == 'POST':
            item = request.form['item']
            type_ = request.form['type']
            qty = int(request.form['qty'])
            price = float(request.form['price'])
            photo = request.files['photo']

            cur.execute("UPDATE items SET item = ?, type = ?, qty = ?, avg_buy_price = ? WHERE id = ?",
                        (item, type_, qty, price, item_id))

            if photo and photo.filename != '':
                ext = os.path.splitext(photo.filename)[1]
                filename = f"{item_id}{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(filepath)
                cur.execute("UPDATE items SET photo = ? WHERE id = ?", (filename, item_id))

            conn.commit()
            return redirect(url_for('items'))

        cur.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = cur.fetchone()

    return render_template('add_item.html', item=item)

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    if not session.get('logged_in'):
        return redirect('/')

    with sqlite3.connect('inventory.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT photo FROM items WHERE id = ?", (item_id,))
        row = cur.fetchone()
        if row and row[0]:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], row[0]))
            except FileNotFoundError:
                pass

        cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()

    return redirect(url_for('items'))


@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if not session.get('logged_in') or session.get('level') != 'Admin':
        return redirect(url_for('login'))

    edit_user = None

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        level = request.form['level']
        original_username = request.form.get('original_username')

        with sqlite3.connect('inventory.db') as conn:
            cur = conn.cursor()
            if original_username and original_username != '':
                # Edit existing user
                if password:
                    hashed_pw = generate_password_hash(password)
                    cur.execute("UPDATE users SET name=?, username=?, password=?, level=? WHERE username=?",
                                (name, username, hashed_pw, level, original_username))
                else:
                    cur.execute("UPDATE users SET name=?, username=?, level=? WHERE username=?",
                                (name, username, level, original_username))
            else:
                # Add new user
                hashed_pw = generate_password_hash(password)
                cur.execute("INSERT INTO users (name, username, password, level) VALUES (?, ?, ?, ?)",
                            (name, username, hashed_pw, level))
            conn.commit()
        return redirect(url_for('manage_users'))

    # GET: Fetch user list and optionally user for edit
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        edit_username = request.args.get('edit')
        if edit_username:
            cur.execute("SELECT * FROM users WHERE username=?", (edit_username,))
            edit_user = cur.fetchone()

    return render_template('manage_users.html', users=users, edit_user=edit_user)


@app.route('/incoming', methods=['GET', 'POST'])
def incoming():
    if not session.get('logged_in'):
        return redirect('/')

    if request.method == 'POST':
        entry_date = request.form['entry_date']
        with sqlite3.connect('inventory.db') as conn:
            cur = conn.cursor()
            i = 0
            while True:
                item = request.form.get(f'item_{i}')
                if item is None:
                    break  # No more rows

                item = item.strip()
                type_ = request.form.get(f'type_{i}', '').strip()
                qty = request.form.get(f'qty_{i}', '').strip()
                price = request.form.get(f'price_{i}', '').strip()

                if item and type_ and qty and price:
                    qty = int(qty)
                    price = float(price)

                    # Check if item exists
                    cur.execute("SELECT id FROM items WHERE item = ? AND type = ?", (item, type_))
                    result = cur.fetchone()

                    if result:
                        itemid = result[0]
                        cur.execute("UPDATE items SET qty = qty + ? WHERE id = ?", (qty, itemid))
                    else:
                        cur.execute("INSERT INTO items (item, type, qty, avg_buy_price) VALUES (?, ?, ?, ?)",
                                    (item, type_, 0, price))
                        itemid = cur.lastrowid

                    # Record in incoming
                    cur.execute("INSERT INTO incoming (date, itemid, item, type, qty, buyprice) VALUES (?, ?, ?, ?, ?, ?)",
                                (entry_date, itemid, item, type_, qty, price))
                i += 1

            conn.commit()
        return redirect(url_for('incoming'))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('incoming.html', today=today)


@app.route('/outgoing', methods=['GET', 'POST'])
def outgoing():
    if not session.get('logged_in'):
        return redirect('/')

    if request.method == 'POST':
        entry_date = request.form['entry_date']
        with sqlite3.connect('inventory.db') as conn:
            cur = conn.cursor()
            i = 0
            while True:
                item = request.form.get(f'item_{i}')
                if item is None:
                    break  # End of entries

                item = item.strip()
                type_ = request.form.get(f'type_{i}', '').strip()
                qty = request.form.get(f'qty_{i}', '').strip()
                price = request.form.get(f'price_{i}', '').strip()

                if item and type_ and qty and price:
                    qty = int(qty)
                    price = float(price)

                    # Check if item exists
                    cur.execute("SELECT id FROM items WHERE item = ? AND type = ?", (item, type_))
                    result = cur.fetchone()

                    if result:
                        itemid = result[0]
                        cur.execute("UPDATE items SET qty = qty - ? WHERE id = ?", (qty, itemid))
                    else:
                        cur.execute("INSERT INTO items (item, type, qty, avg_buy_price) VALUES (?, ?, ?, ?)",
                                    (item, type_, 0, price))
                        itemid = cur.lastrowid

                    # Record in outgoing
                    cur.execute("INSERT INTO outgoing (date, itemid, item, type, qty, sellprice) VALUES (?, ?, ?, ?, ?, ?)",
                                (entry_date, itemid, item, type_, qty, price))
                i += 1

            conn.commit()
        return redirect(url_for('outgoing'))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('outgoing.html', today=today)



@app.route('/suggest_items')
def suggest_items():
    q = request.args.get('q', '')
    with sqlite3.connect('inventory.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT item FROM items WHERE item LIKE ? LIMIT 5", (f'%{q}%',))
        return jsonify([r[0] for r in cur.fetchall()])

@app.route('/suggest_types')
def suggest_types():
    q = request.args.get('q', '')
    with sqlite3.connect('inventory.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT type FROM items WHERE type LIKE ? LIMIT 5", (f'%{q}%',))
        return jsonify([r[0] for r in cur.fetchall()])

@app.route('/incoming_groups')
def incoming_groups():
    if not session.get('logged_in'):
        return redirect('/')
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT date FROM incoming ORDER BY date DESC")
        dates = cur.fetchall()
    return render_template('incoming_groups.html', dates=dates)

@app.route('/edit_incoming_group/<date>', methods=['GET', 'POST'])
def edit_incoming_group(date):
    if not session.get('logged_in'):
        return redirect('/')

    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if request.method == 'POST':
            cur.execute("DELETE FROM incoming WHERE date = ?", (date,))
            i = 0
            while True:
                item = request.form.get(f'item_{i}')
                type_ = request.form.get(f'type_{i}')
                qty = request.form.get(f'qty_{i}')
                price = request.form.get(f'price_{i}')
                if not item:
                    break
                qty = int(qty)
                price = float(price)

                # Check item ID
                cur.execute("SELECT id FROM items WHERE item=? AND type=?", (item, type_))
                row = cur.fetchone()
                if row:
                    itemid = row[0]
                else:
                    cur.execute("INSERT INTO items (item, type, qty, avg_buy_price) VALUES (?, ?, ?, ?)",
                                (item, type_, 0, price))
                    itemid = cur.lastrowid

                cur.execute("INSERT INTO incoming (date, itemid, item, type, qty, buyprice) VALUES (?, ?, ?, ?, ?, ?)",
                            (date, itemid, item, type_, qty, price))
                i += 1

            conn.commit()
            return redirect(url_for('incoming_groups'))

        cur.execute("SELECT * FROM incoming WHERE date = ?", (date,))
        entries = cur.fetchall()

    return render_template("edit_incoming_group.html", date=date, entries=entries)


@app.route('/delete_incoming_group/<date>')
def delete_incoming_group(date):
    if not session.get('logged_in'):
        return redirect('/')
    with sqlite3.connect('inventory.db') as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM incoming WHERE date = ?", (date,))
        conn.commit()
    return redirect(url_for('incoming_groups'))


@app.route('/logout')
def do_logout():
    session.clear()
    return redirect(url_for('login'))


init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
