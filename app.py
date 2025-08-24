from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Photo {self.title}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    session_type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Order {self.name} - {self.session_type}>'

@app.route('/')
def index():
    featured_photos = Photo.query.filter_by(featured=True).limit(6).all()
    categories = db.session.query(Photo.category).distinct().all()
    categories = [cat[0] for cat in categories]
    return render_template('index.html', featured_photos=featured_photos, categories=categories)

@app.route('/portfolio')
def portfolio():
    category = request.args.get('category', 'all')
    if category == 'all':
        photos = Photo.query.order_by(Photo.created_at.desc()).all()
    else:
        photos = Photo.query.filter_by(category=category).order_by(Photo.created_at.desc()).all()
    
    categories = db.session.query(Photo.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('portfolio.html', photos=photos, categories=categories, current_category=category)

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        session_type = request.form['session_type']
        date = request.form['date']
        location = request.form['location']
        message = request.form['message']
        
        # Конвертируем строку даты в объект date
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты!')
            return redirect(url_for('order'))
        
        new_order = Order(
            name=name,
            email=email,
            phone=phone,
            session_type=session_type,
            date=date_obj,
            location=location,
            message=message
        )
        
        try:
            db.session.add(new_order)
            db.session.commit()
            flash('Заказ успешно отправлен! Мы свяжемся с вами в ближайшее время.')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при отправке заказа. Попробуйте еще раз.')
    
    return render_template('order.html')

@app.route('/admin')
def admin():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Доступ запрещен!')
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    photos = Photo.query.order_by(Photo.created_at.desc()).all()
    users = User.query.all()
    
    return render_template('admin.html', orders=orders, photos=photos, users=users)

@app.route('/admin/orders')
def admin_orders():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Доступ запрещен!')
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/photos')
def admin_photos():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Доступ запрещен!')
        return redirect(url_for('index'))
    
    photos = Photo.query.order_by(Photo.created_at.desc()).all()
    return render_template('admin_photos.html', photos=photos)

@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Доступ запрещен!')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'confirmed', 'completed', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Статус заказа #{order_id} обновлен на "{new_status}"')
    
    return redirect(url_for('admin_orders'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Пользователь с таким именем уже существует!')
            return redirect(url_for('register'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Пользователь с таким email уже существует!')
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=password_hash)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти.')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при регистрации. Попробуйте еще раз.')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'Добро пожаловать, {username}!')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Создаем админа по умолчанию, если его нет
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_password = generate_password_hash('admin123')
            admin_user = User(
                username='admin',
                email='admin@portfolio.com',
                password_hash=admin_password,
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print('Создан админ: username=admin, password=admin123')
        
        # Добавляем тестовые фотографии, если их нет
        if Photo.query.count() == 0:
            sample_photos = [
                Photo(title='Портрет в студии', description='Классический портрет', filename='portrait1.jpg', category='Портрет', price=1500, featured=True),
                Photo(title='Свадебная фотосессия', description='Романтичные моменты', filename='wedding1.jpg', category='Свадьба', price=5000, featured=True),
                Photo(title='Семейная фотосессия', description='Теплые семейные кадры', filename='family1.jpg', category='Семья', price=3000, featured=True),
                Photo(title='Пейзажная фотография', description='Красота природы', filename='landscape1.jpg', category='Пейзаж', price=800, featured=True),
                Photo(title='Модная фотосессия', description='Современная мода', filename='fashion1.jpg', category='Мода', price=2500, featured=True),
                Photo(title='Детская фотосессия', description='Невинность детства', filename='children1.jpg', category='Дети', price=2000, featured=True),
            ]
            
            for photo in sample_photos:
                db.session.add(photo)
            
            db.session.commit()
            print('Добавлены тестовые фотографии')
    
    app.run(debug=True)


