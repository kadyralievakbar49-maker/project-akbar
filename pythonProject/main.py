from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-forum-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_moderator = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True)
    likes = db.relationship('Like', backref='post', lazy=True)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)
    edited_by_admin = db.Column(db.Boolean, default=False)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='_user_post_like'),)


# Данные экстренных служб
EMERGENCY_SERVICES = [
    {"name": "Пожарная охрана", "phone": "101"},
    {"name": "Милиция", "phone": "102"},
    {"name": "Скорая помощь", "phone": "103"},
    {"name": "Служба газа", "phone": "104"}
]

# Создание базы данных
with app.app_context():
    db.create_all()


# Декоратор для проверки прав администратора
def admin_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему.')
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])

        # Проверка: пользователь существует в базе данных
        if not user:
            flash('Пользователь не найден. Пожалуйста, войдите снова.')
            session.pop('user_id', None)
            session.pop('username', None)
            session.pop('is_admin', None)
            return redirect(url_for('login'))

        if not user.is_admin:
            flash('У вас нет прав администратора!')
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    wrap.__name__ = f.__name__
    return wrap


# Декоратор для проверки прав модератора или администратора
def moderator_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему.')
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])

        if not user:
            flash('Пользователь не найден. Пожалуйста, войдите снова.')
            session.pop('user_id', None)
            session.pop('username', None)
            session.pop('is_admin', None)
            return redirect(url_for('login'))

        if not user.is_admin and not user.is_moderator:
            flash('У вас нет прав модератора!')
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    wrap.__name__ = f.__name__
    return wrap


# ИИ-ассистент (симуляция для бесплатной версии)
def ai_assistant_response(comment_text, post_title):
    """Генерирует полезный ответ ИИ на основе комментария"""

    # Анализируем тональность комментария
    comment_lower = comment_text.lower()

    # Шаблоны ответов для разных ситуаций
    if any(word in comment_lower for word in ['помощь', 'помогите', 'не знаю', 'совет', 'как']):
        responses = [
            f"💡 Совет по теме '{post_title}': Попробуйте сначала изучить официальную документацию. Часто ответы на базовые вопросы уже есть там!",
            f"🔍 Рекомендую поискать похожие проблемы на форуме. Возможно, кто-то уже сталкивался с этим!",
            f"📚 Для решения подобных задач полезно ознакомиться с основами. Начните с простых примеров и постепенно усложняйте задачу."
        ]
    elif any(word in comment_lower for word in ['ошибка', 'баг', 'не работает', 'сломалось', 'проблема']):
        responses = [
            f"🛠️ При возникновении ошибок: 1) Проверьте логи, 2) Убедитесь, что все зависимости установлены, 3) Попробуйте воспроизвести проблему на чистом окружении.",
            f"🐞 Совет по отладке: добавьте больше логов в код, чтобы отследить, на каком этапе возникает проблема. Часто причина скрыта в неожиданном месте!",
            f"✅ Проверьте распространённые причины: опечатки в коде, неправильные пути к файлам, устаревшие версии библиотек."
        ]
    elif any(word in comment_lower for word in ['спасибо', 'благодарю', 'отлично', 'класс', 'понял']):
        responses = [
            f"😊 Рад, что помог! Если возникнут ещё вопросы — обращайтесь. Обучение — это процесс, и у всех бывают трудности.",
            f"🌟 Отлично, что разобрались! Теперь вы сможете помочь другим участникам форума с похожими вопросами.",
            f"🚀 Продолжайте в том же духе! Каждая решённая проблема делает вас лучше как специалиста."
        ]
    elif any(word in comment_lower for word in ['безопасность', 'пароль', 'данные', 'хакер', 'угроза']):
        responses = [
            f"🔒 Важно помнить: никогда не храните пароли в открытом виде. Всегда используйте хеширование (например, bcrypt) и HTTPS для передачи данных.",
            f"🛡️ Для защиты от атак: регулярно обновляйте зависимости, используйте параметризованные запросы против SQL-инъекций, и ограничивайте права доступа.",
            f"⚠️ Будьте осторожны с личными данными! Никогда не публикуйте реальные пароли, ключи API или конфиденциальную информацию в публичных обсуждениях."
        ]
    else:
        responses = [
            f"🤔 Интересная мысль! Добавлю, что в контексте '{post_title}' также важно учитывать...",
            f"💡 Дополню ваш комментарий: многие сталкиваются с подобным. Полезный лайфхак — ...",
            f"📚 Если хотите глубже изучить тему '{post_title}', рекомендую посмотреть материалы по...",
            f"✨ Ваш комментарий поднимает важный аспект. Стоит также обратить внимание на..."
        ]

    return random.choice(responses) + " 🤖"


# Главная страница
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts, emergency_services=EMERGENCY_SERVICES)


# Регистрация
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


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            session['is_moderator'] = user.is_moderator
            flash('Вы успешно вошли!')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!')

    return render_template('login.html', emergency_services=EMERGENCY_SERVICES)


# Выход
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    session.pop('is_moderator', None)
    flash('Вы успешно вышли!')
    return redirect(url_for('index'))


# Создание поста
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


# Редактирование поста
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)

    if post.user_id != session['user_id'] and not session.get('is_admin'):
        flash('Вы можете редактировать только свои посты!')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title or not content:
            flash('Заголовок и содержание поста обязательны!')
            return redirect(url_for('edit_post', post_id=post_id))

        post.title = title
        post.content = content
        db.session.commit()

        flash('Пост успешно обновлен!')
        return redirect(url_for('view_post', post_id=post_id))

    return render_template('edit_post.html', post=post, emergency_services=EMERGENCY_SERVICES)


# Удаление поста
@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)

    # Проверка: пользователь - автор поста ИЛИ администратор
    if post.user_id != session['user_id'] and not session.get('is_admin'):
        flash('Вы можете удалять только свои посты!')
        return redirect(url_for('index'))

    # Удаляем все комментарии и лайки к посту
    Comment.query.filter_by(post_id=post_id).delete()
    Like.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()

    flash('Пост удален!')
    return redirect(url_for('index'))


# Просмотр поста
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


# Редактирование комментария
@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))

    comment = Comment.query.get_or_404(comment_id)

    # Проверка: пользователь - автор комментария ИЛИ администратор
    if comment.user_id != session['user_id'] and not session.get('is_admin'):
        flash('Вы можете редактировать только свои комментарии!')
        return redirect(url_for('view_post', post_id=comment.post_id))

    if request.method == 'POST':
        content = request.form['content']

        if not content:
            flash('Комментарий не может быть пустым!')
            return redirect(url_for('edit_comment', comment_id=comment_id))

        comment.content = content
        comment.updated_at = datetime.utcnow()

        # Отмечаем, что комментарий отредактирован администратором
        if session.get('is_admin'):
            comment.edited_by_admin = True

        db.session.commit()

        flash('Комментарий успешно обновлен!')
        return redirect(url_for('view_post', post_id=comment.post_id))

    return render_template('edit_comment.html', comment=comment, emergency_services=EMERGENCY_SERVICES)


# Удаление комментария
@app.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))

    comment = Comment.query.get_or_404(comment_id)

    # Проверка: пользователь - автор комментария ИЛИ автор поста ИЛИ администратор
    post = Post.query.get(comment.post_id)
    if comment.user_id != session['user_id'] and post.user_id != session['user_id'] and not session.get('is_admin'):
        flash('Вы можете удалять только свои комментарии или комментарии к своим постам!')
        return redirect(url_for('view_post', post_id=comment.post_id))

    db.session.delete(comment)
    db.session.commit()

    flash('Комментарий удален!')
    return redirect(url_for('view_post', post_id=comment.post_id))


# Лайк поста
@app.route('/like_post/<int:post_id>')
def like_post(post_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему для лайка.')
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)

    # Проверяем, лайкал ли пользователь уже этот пост
    existing_like = Like.query.filter_by(user_id=session['user_id'], post_id=post_id).first()

    if existing_like:
        # Удаляем лайк (дизлайк)
        db.session.delete(existing_like)
        flash('Лайк удален!')
    else:
        # Добавляем лайк
        new_like = Like(user_id=session['user_id'], post_id=post_id)
        db.session.add(new_like)
        flash('Пост понравился!')

    db.session.commit()
    return redirect(url_for('view_post', post_id=post_id))


# Маршрут для ИИ-ассистента
@app.route('/ai_assistant/<int:comment_id>')
def ai_assistant(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post = Post.query.get(comment.post_id)

    # Генерируем ответ ИИ
    ai_response = ai_assistant_response(comment.content, post.title)

    return jsonify({
        'success': True,
        'response': ai_response,
        'comment_id': comment_id
    })


# ==================== АДМИН-ПАНЕЛЬ ====================

# Панель администратора - главная страница
@app.route('/admin')
@admin_required
def admin_panel():
    users = User.query.order_by(User.created_at.desc()).all()
    posts = Post.query.order_by(Post.created_at.desc()).all()
    comments = Comment.query.order_by(Comment.created_at.desc()).all()

    # Статистика
    total_users = len(users)
    total_posts = len(posts)
    total_comments = len(comments)
    total_likes = Like.query.count()

    return render_template('admin.html',
                           users=users,
                           posts=posts,
                           comments=comments,
                           total_users=total_users,
                           total_posts=total_posts,
                           total_comments=total_comments,
                           total_likes=total_likes,
                           emergency_services=EMERGENCY_SERVICES)


# Все посты (для админа)
@app.route('/admin/posts')
@admin_required
def admin_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin_posts.html', posts=posts, emergency_services=EMERGENCY_SERVICES)


# Все комментарии (для админа)
@app.route('/admin/comments')
@admin_required
def admin_comments():
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('admin_comments.html', comments=comments, emergency_services=EMERGENCY_SERVICES)


# Все пользователи (для админа)
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users, emergency_services=EMERGENCY_SERVICES)


# Сделать пользователя администратором
@app.route('/admin/make_admin/<int:user_id>')
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'✅ Пользователь {user.username} теперь администратор!')
    return redirect(url_for('admin_users'))


# Убрать права администратора
@app.route('/admin/remove_admin/<int:user_id>')
@admin_required
def remove_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['user_id']:
        flash('❌ Вы не можете убрать права у себя!')
        return redirect(url_for('admin_users'))
    user.is_admin = False
    db.session.commit()
    flash(f'✅ Права администратора у пользователя {user.username} удалены!')
    return redirect(url_for('admin_users'))


# Сделать пользователя модератором
@app.route('/admin/make_moderator/<int:user_id>')
@admin_required
def make_moderator(user_id):
    user = User.query.get_or_404(user_id)
    user.is_moderator = True
    db.session.commit()
    flash(f'✅ Пользователь {user.username} теперь модератор!')
    return redirect(url_for('admin_users'))


# Убрать права модератора
@app.route('/admin/remove_moderator/<int:user_id>')
@admin_required
def remove_moderator(user_id):
    user = User.query.get_or_404(user_id)
    user.is_moderator = False
    db.session.commit()
    flash(f'✅ Права модератора у пользователя {user.username} удалены!')
    return redirect(url_for('admin_users'))


# Удалить пользователя (админ)
@app.route('/admin/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['user_id']:
        flash('❌ Вы не можете удалить себя!')
        return redirect(url_for('admin_users'))

    username = user.username

    # Удаляем все посты пользователя
    posts = Post.query.filter_by(user_id=user_id).all()
    for post in posts:
        Comment.query.filter_by(post_id=post.id).delete()
        Like.query.filter_by(post_id=post.id).delete()
        db.session.delete(post)

    # Удаляем все комментарии пользователя
    Comment.query.filter_by(user_id=user_id).delete()

    # Удаляем лайки пользователя
    Like.query.filter_by(user_id=user_id).delete()

    # Удаляем пользователя
    db.session.delete(user)
    db.session.commit()

    flash(f'✅ Пользователь {username} удален!')
    return redirect(url_for('admin_users'))


# Удалить пост (админ)
@app.route('/admin/delete_post/<int:post_id>')
@admin_required
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    Comment.query.filter_by(post_id=post_id).delete()
    Like.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()

    flash('✅ Пост удален администратором!')
    return redirect(url_for('admin_posts'))


# Удалить комментарий (админ)
@app.route('/admin/delete_comment/<int:comment_id>')
@admin_required
def admin_delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()

    flash('✅ Комментарий удален администратором!')
    return redirect(url_for('admin_comments'))


# Редактировать комментарий (админ)
@app.route('/admin/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if request.method == 'POST':
        content = request.form['content']

        if not content:
            flash('❌ Комментарий не может быть пустым!')
            return redirect(url_for('admin_edit_comment', comment_id=comment_id))

        comment.content = content
        comment.updated_at = datetime.utcnow()
        comment.edited_by_admin = True

        db.session.commit()

        flash('✅ Комментарий успешно обновлен администратором!')
        return redirect(url_for('admin_comments'))

    return render_template('admin_edit_comment.html', comment=comment, emergency_services=EMERGENCY_SERVICES)


# Редактировать пост (админ)
@app.route('/admin/edit_post/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title or not content:
            flash('❌ Заголовок и содержание поста обязательны!')
            return redirect(url_for('admin_edit_post', post_id=post_id))

        post.title = title
        post.content = content

        db.session.commit()

        flash('✅ Пост успешно обновлен администратором!')
        return redirect(url_for('admin_posts'))

    return render_template('admin_edit_post.html', post=post, emergency_services=EMERGENCY_SERVICES)


# Мой профиль
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # Проверка: пользователь существует в базе данных
    if not user:
        flash('Пользователь не найден. Пожалуйста, войдите снова.')
        session.pop('user_id', None)
        session.pop('username', None)
        session.pop('is_admin', None)
        return redirect(url_for('login'))

    return render_template('profile.html', user=user, emergency_services=EMERGENCY_SERVICES)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)