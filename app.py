import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import boto3
import uuid
from dotenv import load_dotenv
load_dotenv()


# -----------------------------------------
# Flask + Config
# -----------------------------------------
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# -----------------------------------------
# S3 Upload Helper
# -----------------------------------------
def upload_to_s3(file):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"],
        region_name=app.config["AWS_REGION"]
    )

    filename = f"{uuid.uuid4().hex}_{file.filename}"

    s3.upload_fileobj(
        file,
        app.config["AWS_S3_BUCKET"],
        filename,
        ExtraArgs={"ACL": "public-read"}
    )

    return f"https://{app.config['AWS_S3_BUCKET']}.s3.amazonaws.com/{filename}"

# -----------------------------------------
# SQLAlchemy Models
# -----------------------------------------
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(200), nullable=False)
    qty = db.Column(db.Integer, default=0)
    avg_buy_price = db.Column(db.Float)
    photo = db.Column(db.String(500))   # S3 URL

class Incoming(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    itemid = db.Column(db.Integer)
    item = db.Column(db.String(200))
    type = db.Column(db.String(200))
    qty = db.Column(db.Integer)
    buyprice = db.Column(db.Float)

class Outgoing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    itemid = db.Column(db.Integer)
    item = db.Column(db.String(200))
    type = db.Column(db.String(200))
    qty = db.Column(db.Integer)
    sellprice = db.Column(db.Float)

class User(db.Model):
    name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(200), primary_key=True)
    password = db.Column(db.String(500), nullable=False)
    level = db.Column(db.String(10), nullable=False)

# -----------------------------------------
# Initialize DB (only once)
# -----------------------------------------
@app.before_request
def init_db():
    db.create_all()

    # Default admin user
    if not User.query.filter_by(username='Admin').first():
        hashed_pw = generate_password_hash("Bhaskar123")
        admin = User(name="Ramanuj", username="Admin", password=hashed_pw, level="Admin")
        db.session.add(admin)
        db.session.commit()

# -----------------------------------------
# Routes
# -----------------------------------------
@app.route('/')
def login():
    return render_template('login.html')


@app.route('/do_login', methods=['POST'])
def do_login():
    user = request.form['username']
    pw = request.form['password']

    # Query using SQLAlchemy instead of sqlite3
    row = User.query.filter_by(username=user).first()

    if row and check_password_hash(row.password, pw):
        session['logged_in'] = True
        session['username'] = row.username
        session['fullname'] = row.name
        session['level'] = row.level
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

    # Get all unique types for dropdown
    all_types = [row.type for row in db.session.query(Item.type).distinct().all()]

    # Base query
    query = Item.query

    # Apply search filter
    if q:
        query = query.filter(Item.item.ilike(f"%{q}%"))

    # Apply type filter
    if item_type:
        query = query.filter_by(type=item_type)

    # Final results
    results = query.all()

    return render_template(
        'items.html',
        items=results,
        query=q,
        selected_type=item_type,
        all_types=all_types
    )

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if not session.get('logged_in'):
        return redirect('/')

    if request.method == 'POST':
        item_name = request.form['item']
        type_ = request.form['type']
        qty = int(request.form['qty'])
        price = float(request.form['price'])
        photo_file = request.files.get('photo')

        # Step 1: Create item WITHOUT photo first, to get ID
        new_item = Item(
            item=item_name,
            type=type_,
            qty=qty,
            avg_buy_price=price,
            photo=None
        )
        db.session.add(new_item)
        db.session.commit()          # Saves and assigns ID
        item_id = new_item.id

        # Step 2: Upload photo to S3
        if photo_file and photo_file.filename != "":
            s3_url = upload_to_s3(photo_file)

            # Update item with photo URL
            new_item.photo = s3_url
            db.session.commit()

        return redirect(url_for('items'))

    return render_template('add_item.html', item=None)


@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if not session.get('logged_in'):
        return redirect('/')

    # Fetch the item using SQLAlchemy
    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        item_name = request.form['item']
        type_ = request.form['type']
        qty = int(request.form['qty'])
        price = float(request.form['price'])
        photo_file = request.files.get('photo')

        # Update item values
        item.item = item_name
        item.type = type_
        item.qty = qty
        item.avg_buy_price = price

        # Upload new photo to S3 if provided
        if photo_file and photo_file.filename != "":
            s3_url = upload_to_s3(photo_file)
            item.photo = s3_url

        db.session.commit()
        return redirect(url_for('items'))

    return render_template('add_item.html', item=item)


@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    if not session.get('logged_in'):
        return redirect('/')

    # Fetch the item
    item = Item.query.get_or_404(item_id)

    # If item has a photo URL → delete from S3
    if item.photo:
        try:
            # Extract S3 filename from full URL
            bucket = os.getenv("AWS_S3_BUCKET")
            key = item.photo.split(f"https://{bucket}.s3.amazonaws.com/")[-1]

            s3 = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION")
            )

            s3.delete_object(Bucket=bucket, Key=key)

        except Exception as e:
            print("S3 delete failed:", e)

    # Delete the item from DB
    db.session.delete(item)
    db.session.commit()

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

        # If original_username exists → edit mode
        if original_username:
            user = User.query.filter_by(username=original_username).first()

            if user:
                user.name = name
                user.username = username
                user.level = level

                if password:  # update password only if provided
                    user.password = generate_password_hash(password)

                db.session.commit()

        else:
            # Add new user
            hashed_pw = generate_password_hash(password)
            new_user = User(
                name=name,
                username=username,
                password=hashed_pw,
                level=level
            )
            db.session.add(new_user)
            db.session.commit()

        return redirect(url_for('manage_users'))

    # GET logic
    users = User.query.all()

    edit_username = request.args.get('edit')
    if edit_username:
        edit_user = User.query.filter_by(username=edit_username).first()

    return render_template(
        'manage_users.html',
        users=users,
        edit_user=edit_user
    )



@app.route('/incoming', methods=['GET', 'POST'])
def incoming():
    if not session.get('logged_in'):
        return redirect('/')

    if request.method == 'POST':
        entry_date = request.form['entry_date']

        i = 0
        while True:
            item_name = request.form.get(f'item_{i}')
            if item_name is None:
                break  # No more rows

            item_name = item_name.strip()
            type_ = request.form.get(f'type_{i}', '').strip()
            qty = request.form.get(f'qty_{i}', '').strip()
            price = request.form.get(f'price_{i}', '').strip()

            if item_name and type_ and qty and price:
                qty = int(qty)
                price = float(price)

                # 1️⃣ Check if item exists
                existing = Item.query.filter_by(item=item_name, type=type_).first()

                if existing:
                    itemid = existing.id
                    existing.qty += qty     # Update stock
                else:
                    # Create new item
                    new_item = Item(
                        item=item_name,
                        type=type_,
                        qty=0,               # Start at 0 (like your old code)
                        avg_buy_price=price
                    )
                    db.session.add(new_item)
                    db.session.commit()      # Needed to get new_item.id
                    itemid = new_item.id

                # 2️⃣ Insert incoming record
                incoming_entry = Incoming(
                    date=entry_date,
                    itemid=itemid,
                    item=item_name,
                    type=type_,
                    qty=qty,
                    buyprice=price
                )
                db.session.add(incoming_entry)

            i += 1

        # Commit all changes at once
        db.session.commit()

        return redirect(url_for('incoming'))

    # GET: show today's date
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('incoming.html', today=today)



@app.route('/outgoing', methods=['GET', 'POST'])
def outgoing():
    if not session.get('logged_in'):
        return redirect('/')

    if request.method == 'POST':
        entry_date = request.form['entry_date']

        i = 0
        while True:
            item_name = request.form.get(f'item_{i}')
            if item_name is None:
                break

            item_name = item_name.strip()
            type_ = request.form.get(f'type_{i}', '').strip()
            qty = request.form.get(f'qty_{i}', '').strip()
            price = request.form.get(f'price_{i}', '').strip()

            if item_name and type_ and qty and price:
                qty = int(qty)
                price = float(price)

                # 1️⃣ Check if item exists
                existing = Item.query.filter_by(item=item_name, type=type_).first()

                if existing:
                    itemid = existing.id
                    existing.qty -= qty  # Reduce stock
                else:
                    # Create new item with qty=0 (same behavior as old code)
                    new_item = Item(
                        item=item_name,
                        type=type_,
                        qty=0,
                        avg_buy_price=price
                    )
                    db.session.add(new_item)
                    db.session.commit()
                    itemid = new_item.id

                # 2️⃣ Insert outgoing log
                outgoing_entry = Outgoing(
                    date=entry_date,
                    itemid=itemid,
                    item=item_name,
                    type=type_,
                    qty=qty,
                    sellprice=price
                )
                db.session.add(outgoing_entry)

            i += 1

        db.session.commit()
        return redirect(url_for('outgoing'))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('outgoing.html', today=today)




@app.route('/suggest_items')
def suggest_items():
    q = request.args.get('q', '')

    if not q:
        return jsonify([])

    # SQLAlchemy version of: SELECT DISTINCT item FROM items WHERE item LIKE '%q%' LIMIT 5
    results = (
        db.session.query(Item.item)
        .filter(Item.item.ilike(f"%{q}%"))
        .distinct()
        .limit(5)
        .all()
    )

    return jsonify([r[0] for r in results])


@app.route('/suggest_types')
def suggest_types():
    q = request.args.get('q', '')

    if not q:
        return jsonify([])

    results = (
        db.session.query(Item.type)
        .filter(Item.type.ilike(f"%{q}%"))
        .distinct()
        .limit(5)
        .all()
    )

    return jsonify([r[0] for r in results])


@app.route('/incoming_groups')
def incoming_groups():
    if not session.get('logged_in'):
        return redirect('/')

    # SELECT DISTINCT date FROM incoming ORDER BY date DESC
    dates = (
        db.session.query(Incoming.date)
        .distinct()
        .order_by(Incoming.date.desc())
        .all()
    )

    # Convert to match your old template: list of rows/dicts
    dates = [d[0] for d in dates]

    return render_template('incoming_groups.html', dates=dates)


@app.route('/edit_incoming_group/<date>', methods=['GET', 'POST'])
def edit_incoming_group(date):
    if not session.get('logged_in'):
        return redirect('/')

    if request.method == 'POST':
        # 1️⃣ Delete all existing entries for that date
        Incoming.query.filter_by(date=date).delete()

        i = 0
        while True:
            item_name = request.form.get(f'item_{i}')
            if not item_name:
                break

            type_ = request.form.get(f'type_{i}')
            qty = request.form.get(f'qty_{i}')
            price = request.form.get(f'price_{i}')

            qty = int(qty)
            price = float(price)

            # 2️⃣ Find or create Item
            existing = Item.query.filter_by(item=item_name, type=type_).first()

            if existing:
                itemid = existing.id
            else:
                new_item = Item(
                    item=item_name,
                    type=type_,
                    qty=0,
                    avg_buy_price=price
                )
                db.session.add(new_item)
                db.session.commit()
                itemid = new_item.id

            # 3️⃣ Insert new incoming record
            new_entry = Incoming(
                date=date,
                itemid=itemid,
                item=item_name,
                type=type_,
                qty=qty,
                buyprice=price
            )
            db.session.add(new_entry)

            i += 1

        db.session.commit()
        return redirect(url_for('incoming_groups'))

    # GET request — load entries for the date
    entries = Incoming.query.filter_by(date=date).all()

    return render_template(
        "edit_incoming_group.html",
        date=date,
        entries=entries
    )



@app.route('/delete_incoming_group/<date>')
def delete_incoming_group(date):
    if not session.get('logged_in'):
        return redirect('/')

    # Delete all incoming records for the given date
    Incoming.query.filter_by(date=date).delete()
    db.session.commit()

    return redirect(url_for('incoming_groups'))

@app.route('/debug_env')
def debug_env():
    from flask import jsonify
    return jsonify({
        "region": os.getenv("AWS_REGION"),
        "bucket": os.getenv("AWS_S3_BUCKET"),
        "database": os.getenv("DATABASE_URL")[:40] + "..."
    })


@app.route('/logout')
def do_logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
