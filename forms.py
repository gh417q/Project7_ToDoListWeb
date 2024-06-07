from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Optional, Email  # requires "pip install email_validator"
from wtforms.fields import DateField

# RegisterForm to register new users
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("e-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


# LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField("e-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class CreateListForm(FlaskForm):
    name = StringField("List Name", validators=[DataRequired()])
    submit = SubmitField("Create List")


class AddTaskForm(FlaskForm):
    task = StringField("Task", validators=[DataRequired()])
    due = DateField('Due date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField("Add Task")
