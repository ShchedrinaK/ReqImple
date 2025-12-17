from .extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))

    bio = db.Column(db.Text)

    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    ideas = db.relationship('Idea', back_populates='author', lazy=True, cascade='all, delete-orphan')
    implementations = db.relationship('Implementation', back_populates='author', lazy=True,
                                      cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, active, archived
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = db.relationship('User', back_populates='ideas')
    implementations = db.relationship('Implementation', back_populates='idea', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='idea', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Idea {self.title}>'


class Implementation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    external_url = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), default='other')  # github_repo, etc.
    status = db.Column(db.String(20), default='pending')  # pending, verified, hidden
    idea_source_id = db.Column(db.Integer, db.ForeignKey('idea.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    idea = db.relationship('Idea', back_populates='implementations')
    author = db.relationship('User', back_populates='implementations')
    comments = db.relationship('Comment', back_populates='implementation', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Implementation {self.title}>'


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

    # Для полиморфной связи с идеями или реализациями
    parent_type = db.Column(db.String(20), nullable=False)  # 'idea' or 'implementation'
    parent_id = db.Column(db.Integer, nullable=False)  # ID of parent (Idea or Implementation)

    # Внешние ключи и отношения для конкретных типов
    idea_id = db.Column(db.Integer, db.ForeignKey('idea.id', ondelete='CASCADE'), nullable=True)
    implementation_id = db.Column(db.Integer, db.ForeignKey('implementation.id', ondelete='CASCADE'), nullable=True)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', back_populates='comments')

    # Для идей
    idea = db.relationship('Idea', back_populates='comments', foreign_keys=[idea_id])

    # Для реализаций
    implementation = db.relationship('Implementation', back_populates='comments', foreign_keys=[implementation_id])

    def __repr__(self):
        return f'<Comment {self.id} by {self.author.username}>'
