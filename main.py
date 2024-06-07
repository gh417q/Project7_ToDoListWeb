from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, UniqueConstraint, nullslast
from forms import RegisterForm, LoginForm, CreateListForm, AddTaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# LOGIN
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///to_do_lists.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class List(db.Model):
    __tablename__ = "lists"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(50), unique=True, nullable=False)
    owner_id = mapped_column(ForeignKey("users.id"))  # table name, not class
    owner = relationship("User", back_populates="lists")
    tasks = relationship("Task", back_populates="list")
    created = mapped_column(String(20), unique=False, nullable=True)


class Task(db.Model):
    __tablename__ = "tasks"
    id = mapped_column(Integer, primary_key=True)
    task = mapped_column(String(250), unique=False, nullable=False)
    done = mapped_column(Boolean, unique=False, default=False, nullable=False)
    due = mapped_column(String(20), unique=False, nullable=True)
    list_id = mapped_column(ForeignKey("lists.id"))  # table name, not class
    list = relationship("List", back_populates="tasks")
    owner_id = mapped_column(ForeignKey("users.id"))  # table name, not class
    owner = relationship("User", back_populates="tasks")
    UniqueConstraint('task', 'list_id', name='idx_list-id_task')


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), nullable=False)
    email = mapped_column(String(100), unique=True, nullable=False)
    password = mapped_column(String(100), nullable=False)
    lists = relationship("List", back_populates="owner")
    tasks = relationship("Task", back_populates="owner")


with app.app_context():
    db.create_all()


# Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user with this e-mail already exists
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user is not None:
            flash(f"User {form.email.data} already exists, please login.")
            return render_template("login.html", form=LoginForm())
        new_user_password = form.password.data
        hash_pwd = generate_password_hash(new_user_password, method='pbkdf2', salt_length=8)
        new_user = User(name=form.name.data, password=hash_pwd, email=form.email.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)  # flask_login method, so it can proceed where "login is required" and be traced
        return redirect(url_for('get_all_lists'))  # home
    return render_template("register.html", form=form)


# Retrieve a user from the database based on their email.
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user is None:
            flash(f"User {form.email.data} doesn't exist, please register or login as different user.")
            return redirect(url_for('login'))
        if not check_password_hash(pwhash=user.password, password=form.password.data):
            flash("Login unsuccessful, please register or try again.")
            return redirect(url_for('login'))
        login_user(user)  # flask_login method, so it can proceed where "login is required" and be traced
        return redirect(url_for('get_all_lists'))  # home
    return render_template("login.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_lists'))


@app.route('/')
def get_all_lists():
    if current_user.is_authenticated:
        result = db.session.execute(db.select(List).where(List.owner_id == current_user.get_id()))
        lists = result.scalars().all()
        return render_template("index.html", all_lists=lists)
    return redirect(url_for('login'))


@app.route("/new-list", methods=["GET", "POST"])
@login_required
def add_new_list():
    form = CreateListForm()
    if form.validate_on_submit():
        list = db.session.execute(db.select(List).where(List.name == form.name.data)).scalar()
        if list is None:
            new_list = List(
                name=form.name.data,
                owner=current_user,
                created=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_list)
            db.session.commit()
            return redirect(url_for("add_task", list_id=new_list.id))
        flash(f"List '{form.name.data}' already exists, please use different name.")
    return render_template("add-list.html", form=form)


@app.route("/list/<int:list_id>", methods=["GET", "POST"])
@login_required
def add_task(list_id):
    requested_list = db.get_or_404(List, list_id)
    form = AddTaskForm()
    if form.validate_on_submit():
        task = db.session.execute(db.select(Task).where(Task.task == form.task.data).where(Task.list_id == list_id)).scalar()
        if task is None:
            db.session.add(Task(task=form.task.data, due=form.due.data, owner_id=current_user.get_id(), list_id=list_id))
            db.session.commit()
        else:
            flash(f"Task '{form.task.data}' already exists in this list.")
    tasks = db.session.execute(db.select(Task).order_by(nullslast(Task.due)).where(Task.list_id == list_id)).scalars().all()
    return render_template("to_do_list.html", list=requested_list, form=form, tasks=tasks)


@app.route("/delete/<int:list_id>")
@login_required
def delete_list(list_id):
    list_to_delete = db.get_or_404(List, list_id)
    db.session.delete(list_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_lists'))


@app.route("/delete_task/<int:task_id>")
@login_required
def delete_task(task_id):
    task_to_delete = db.get_or_404(Task, task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for("add_task", list_id=task_to_delete.list_id))


@app.route("/task_completion/<int:task_id>")
@login_required
def update_task_completion(task_id):
    task_to_update = db.get_or_404(Task, task_id)
    # print(f"task completion: ID {task_id}, completed {task_to_update.done}")
    task_to_update.done = not task_to_update.done
    db.session.commit()
    return redirect(url_for("add_task", list_id=task_to_update.list_id))


if __name__ == "__main__":
    app.run(debug=True, port=5002)
