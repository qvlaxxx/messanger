from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user, LoginManager # pip install flask-login
from database import Session, Users, Friends, Messages
from flask_wtf.csrf import CSRFProtect
from logging.handlers import RotatingFileHandler
import logging
import threading
import unittest

file_handler = RotatingFileHandler(
    'app.log', 
    maxBytes=1_000,
    encoding='utf-8'
)
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s (%(pathname)s:%(lineno)d): %(message)s'
)
file_handler.setFormatter(formatter)

app = Flask(__name__)
app.logger.addHandler(file_handler)
app.logger.setLevel("INFO")
csrf = CSRFProtect(app)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['MAX_FORM_MEMORY_SIZE'] = 1024 * 1024  # 1MB
app.config['MAX_FORM_PARTS'] = 500
app.config['SECRET_KEY'] = '#cv)3v7w$*s3fk;5c!@y0?:?№3"9)#'
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Забороняє доступ JS до cookie (захист від XSS)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Захист від CSRF

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


login_manager.login_view = 'login'

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

@login_manager.user_loader
def load_user(user_id):
  with Session() as session:
    user = session.query(Users).filter_by(id = user_id).first()
    if user:
      return user
    
@app.route("/")
def base():
  app.logger.info("User opened the home.")
  return render_template("home.html")

@app.route("/chat")
def messages():
    app.logger.info("User opened the chat.")
    return render_template("chat.html")

@app.route("/friends")
def friends():
    app.logger.info("User opened the friends list.")
    return render_template("friends.html")

@app.route("/login", methods = ["GET","POST"])
def login():
    app.logger.info("User opened the login.")
    if request.method == 'POST':
        nickname = request.form['nickname']
        password = request.form['password']

        with Session() as session:
            user = session.query(Users).filter_by(nickname = nickname).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('home'))
            app.logger.warning(f"Failed login attempt for nickname: {nickname}")
            flash('Неправильний nickname або пароль!', 'danger')
    return render_template('login.html')

@app.route("/register", methods = ["GET","POST"])
def register():
    app.logger.info("User opened the register.")
    if request.method == 'POST':
        nickname = request.form['nickname']
        password = request.form['password']
        email = request.form['email']     
        with Session() as session:
            user = session.query(Users).filter_by(nickname=nickname).first()
            if user:
                app.logger.warning(f"Attempt to register with existing nickname: {nickname}")
                flash('Користувач з таким іменем вже існує!', 'danger')
                return redirect(url_for('register'))
            new_user = Users(nickname=nickname, email=email)
            new_user.set_password(password)
            session.add(new_user)
            session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    app.logger.info(f"User {current_user.nickname} logged out.")
    logout_user()
    return redirect(url_for('login'))


class TestFlask(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_status(self):
        response = self.client.get('/friends')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/chat')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

unittest.main(argv=['first-arg-is-ignored'], exit=False)

# if __name__ == "__main__":
#   app.run(debug=True)
