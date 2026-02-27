from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-forum-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

EMERGENCY_SERVICES = [
    {"name": "Пожарная охрана", "phone": "101"},
    {"name": "Милиция", "phone": "102"},
    {"name": "Скорая помощь", "phone": "103"},
    {"name": "Служба газа", "phone": "104"}
]

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts, emergency_services=EMERGENCY_SERVICES)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует!')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Пользователь с такой почтой уже существует!')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.')
        return redirect(url_for('login'))
    return render_template('register.html', emergency_services=EMERGENCY_SERVICES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Вы успешно вошли!')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!')
    return render_template('login.html', emergency_services=EMERGENCY_SERVICES)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Вы успешно вышли!')
    return redirect(url_for('index'))

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему для создания поста.')
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title or not content:
            flash('Заголовок и содержание поста обязательны!')
            return redirect(url_for('create_post'))
        new_post = Post(title=title, content=content, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        flash('Пост успешно создан!')
        return redirect(url_for('index'))
    return render_template('create_post.html', emergency_services=EMERGENCY_SERVICES)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        content = request.form['content']
        is_anonymous = request.form.get('is_anonymous') == 'on'
        if not content:
            flash('Комментарий не может быть пустым!')
            return redirect(url_for('view_post', post_id=post_id))
        if is_anonymous:
            new_comment = Comment(content=content, post_id=post_id, is_anonymous=True)
        else:
            if 'user_id' not in session:
                flash('Пожалуйста, войдите в систему или отметьте "Анонимно".')
                return redirect(url_for('login'))
            new_comment = Comment(content=content, user_id=session['user_id'], post_id=post_id, is_anonymous=False)
        db.session.add(new_comment)
        db.session.commit()
        flash('Комментарий добавлен!')
        return redirect(url_for('view_post', post_id=post_id))
    return render_template('view_post.html', post=post, emergency_services=EMERGENCY_SERVICES)

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    if post.user_id != session['user_id']:
        flash('Вы можете удалять только свои посты!')
        return redirect(url_for('index'))
    Comment.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    flash('Пост удален!')
    return redirect(url_for('index'))

@app.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))
    comment = Comment.query.get_or_404(comment_id)
    post = Post.query.get(comment.post_id)
    if comment.user_id != session['user_id'] and post.user_id != session['user_id']:
        flash('Вы можете удалять только свои комментарии или комментарии к своим постам!')
        return redirect(url_for('view_post', post_id=comment.post_id))
    db.session.delete(comment)
    db.session.commit()
    flash('Комментарий удален!')
    return redirect(url_for('view_post', post_id=comment.post_id))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user, emergency_services=EMERGENCY_SERVICES)

if __name__ == '__main__':
    app.run(debug=True)