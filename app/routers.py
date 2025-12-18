from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Idea, Implementation, Comment
from app.forms import RegistrationForm, LoginForm, IdeaForm, CommentForm, ImplementationForm, ProfileForm, EditIdeaForm
import jwt
import os
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

# JWT секрет
JWT_SECRET = os.getenv('SECRET_KEY')


# Вспомогательная функция для JWT
def generate_token(user_id):
    return jwt.encode({'user_id': user_id, 'exp': datetime.utcnow() + timedelta(hours=1)}, JWT_SECRET,
                      algorithm='HS256')


# Публичные маршруты
@bp.route('/')
def index():
    ideas = Idea.query.filter_by(status='active').all()
    return render_template('index.html', ideas=ideas)


@bp.route('/ideas/<int:id>')
def idea_detail(id):
    idea = Idea.query.get_or_404(id)
    comments = Comment.query.filter_by(parent_type='idea', parent_id=id).all()
    form = CommentForm()
    return render_template('idea_detail.html', idea=idea, comments=comments, form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data, display_name=form.display_name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# Защищенные маршруты
@bp.route('/create/idea', methods=['GET', 'POST'])
@login_required
def create_idea():
    form = IdeaForm()
    if form.validate_on_submit():
        idea = Idea(
            title=form.title.data,
            description=form.description.data,
            author=current_user,
            status='active')
        db.session.add(idea)
        db.session.commit()
        flash('Идея успешно создана!', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_idea.html', form=form)


@bp.route('/ideas/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_idea(id):
    """Редактирование идеи"""
    idea = Idea.query.get_or_404(id)

    # Проверяем, что пользователь редактирует свою идею
    if idea.author != current_user and not current_user.is_admin:
        flash('Вы можете редактировать только свои идеи', 'danger')
        return redirect(url_for('main.idea_detail', id=id))

    form = EditIdeaForm(obj=idea)

    if form.validate_on_submit():
        idea.title = form.title.data
        idea.description = form.description.data
        idea.status = form.status.data
        idea.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Идея успешно обновлена!', 'success')
        return redirect(url_for('main.idea_detail', id=id))

    return render_template('edit_idea.html', form=form, idea=idea)


@bp.route('/ideas/<int:id>/create-implementation', methods=['GET', 'POST'])
@login_required
def create_implementation(id):
    """Создание реализации для идеи"""
    idea = Idea.query.get_or_404(id)
    form = ImplementationForm()

    if form.validate_on_submit():
        try:
            implementation = Implementation(
                title=form.title.data,
                description=form.description.data,
                external_url=form.external_url.data,
                type=form.type.data,
                idea_source_id=idea.id,
                author_id=current_user.id,
                status='pending'
            )

            db.session.add(implementation)
            db.session.commit()

            flash('Реализация успешно создана и отправлена на модерацию!', 'success')
            return redirect(url_for('main.idea_detail', id=idea.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании реализации: {str(e)}', 'danger')

    return render_template('create_implementation.html', form=form, idea=idea)


@bp.route('/ideas/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    form = CommentForm()
    if form.validate_on_submit():
        # Создаем комментарий для идеи
        comment = Comment(
            content=form.content.data,
            parent_type='idea',
            parent_id=id,
            author=current_user,
            idea_id=id  # Устанавливаем явно связь с идеей
        )
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен', 'success')
    return redirect(url_for('main.idea_detail', id=id))


@bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Удаление комментария"""
    comment = Comment.query.get_or_404(comment_id)

    if comment.author_id != current_user.id:
        flash('Вы можете удалять только свои комментарии', 'danger')
        return redirect(url_for('main.idea_detail', id=comment.parent_id))

    idea_id = comment.parent_id
    db.session.delete(comment)
    db.session.commit()

    flash('Комментарий удален', 'success')
    return redirect(url_for('main.idea_detail', id=idea_id))


# ============ МАРШРУТЫ ДЛЯ РЕАЛИЗАЦИЙ ============

@bp.route('/implementation/<int:id>')
def implementation_detail(id):
    """Страница детализации реализации"""
    implementation = Implementation.query.get_or_404(id)

    # Получаем комментарии для этой реализации
    comments = Comment.query.filter_by(
        parent_type='implementation',
        parent_id=id
    ).order_by(Comment.created_at.desc()).all()

    return render_template(
        'implementation_detail.html',
        implementation=implementation,
        comments=comments
    )


@bp.route('/implementation/<int:id>/comment', methods=['POST'])
@login_required
def add_implementation_comment(id):
    """Добавление комментария к реализации"""
    implementation = Implementation.query.get_or_404(id)
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            parent_type='implementation',
            parent_id=id,
            author=current_user,
            implementation_id=id  # Устанавливаем явно связь с реализацией
        )
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен', 'success')

    return redirect(url_for('main.implementation_detail', id=id))


@bp.route('/implementation/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_implementation_comment(comment_id):
    """Удаление комментария реализации"""
    comment = Comment.query.get_or_404(comment_id)

    if comment.parent_type != 'implementation':
        flash('Некорректный комментарий', 'danger')
        return redirect(url_for('main.index'))

    if comment.author_id != current_user.id and not current_user.is_admin:
        flash('Вы можете удалять только свои комментарии', 'danger')
        return redirect(url_for('main.implementation_detail', id=comment.parent_id))

    implementation_id = comment.parent_id
    db.session.delete(comment)
    db.session.commit()

    flash('Комментарий удален', 'success')
    return redirect(url_for('main.implementation_detail', id=implementation_id))


# ============ АДМИН МАРШРУТЫ ============

@bp.route('/admin/moderation')
@login_required
def admin_moderation():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))

    # Получаем реализации на модерации
    pending_implementations = Implementation.query.filter_by(status='pending').all()

    # Создаем простой шаблон на лету, если файла нет
    if pending_implementations:
        return render_template('admin_moderation.html', pending=pending_implementations)
    else:
        return "<h1>Админ панель модерации</h1><p>Реализаций на модерации нет.</p>"


@bp.route('/admin/verify/<int:id>')
@login_required
def verify_implementation(id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))

    implementation = Implementation.query.get_or_404(id)

    # Переключаем статус
    if implementation.status == 'verified':
        implementation.status = 'pending'
        message = 'Верификация отменена'
    else:
        implementation.status = 'verified'
        message = 'Реализация верифицирована'

    db.session.commit()
    flash(message, 'success')
    return redirect(url_for('main.admin_moderation'))


# ============ ПРОФИЛЬ И API ============

@bp.route('/@<username>')
def profile(username):
    """Страница профиля пользователя"""
    user = User.query.filter_by(username=username).first_or_404()

    ideas = Idea.query.filter_by(
        author_id=user.id,
        status='active'
    ).order_by(Idea.created_at.desc()).all()

    implementations = Implementation.query.filter_by(
        author_id=user.id,
        status='verified'
    ).order_by(Implementation.created_at.desc()).all()

    stats = {
        'ideas_count': len(ideas),
        'implementations_count': len(implementations),
        'comments_count': len(user.comments) if user.comments else 0,
        'member_since': user.created_at.strftime('%B %Y')
    }

    return render_template(
        'profile.html',
        user=user,
        ideas=ideas,
        implementations=implementations,
        stats=stats
    )


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.display_name = form.display_name.data
        current_user.bio = form.bio.data
        current_user.website_url = form.website_url.data
        current_user.github_username = form.github_username.data

        db.session.commit()
        flash('Профиль обновлен', 'success')
        return redirect(url_for('main.profile', username=current_user.username))

    return render_template('edit_profile.html', form=form)


# API маршруты
@bp.route('/api/v1/ideas', methods=['GET'])
def api_ideas():
    ideas = Idea.query.filter_by(status='active').all()
    return jsonify([{'id': i.id, 'title': i.title, 'author': i.author.username} for i in ideas])


@bp.route('/api/v1/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        token = generate_token(user.id)
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid credentials'}), 401
