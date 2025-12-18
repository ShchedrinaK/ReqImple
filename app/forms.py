from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, URL, Optional


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    display_name = StringField('Display Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class IdeaForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Create Idea')


class EditIdeaForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    status = SelectField('Статус', choices=[
        ('draft', 'Черновик'),
        ('active', 'Активна'),
        ('archived', 'В архиве')
    ], validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')


class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')


class ImplementationForm(FlaskForm):
    title = StringField('Название реализации', validators=[
        DataRequired(),
        Length(max=200, message="Название не должно превышать 200 символов")
    ])

    description = TextAreaField('Описание реализации', validators=[
        DataRequired(),
        Length(min=30, message="Описание должно содержать минимум 30 символов")
    ])

    external_url = StringField('Ссылка', validators=[
        DataRequired(),
        Length(max=500, message="Ссылка слишком длинная")
    ])

    type = SelectField('Тип реализации', choices=[
        ('github_repo', 'GitHub репозиторий'),
        ('live_demo', 'Демо-версия'),
        ('article', 'Статья/объяснение'),
        ('prototype', 'Прототип'),
        ('other', 'Другое')
    ], validators=[DataRequired()])

    submit = SubmitField('Создать реализацию')


class ProfileForm(FlaskForm):
    display_name = StringField('Отображаемое имя', validators=[DataRequired()])
    bio = TextAreaField('О себе')
    website_url = StringField('Сайт', validators=[Optional(), URL()])
    github_username = StringField('GitHub username')
    submit = SubmitField('Сохранить')
