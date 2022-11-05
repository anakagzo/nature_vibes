import requests
from flask import Flask, session, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)

app.config['SECRET_KEY'] = 'bbqrep3690'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


# CREATE TABLE IN DB
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


# Line below only required once, when creating DB.
# db.create_all()


API_path = "http://www.tropicalfruitandveg.com/api/tfvjsonapi.php"
# fv means fruit and veggie
fv_list = ['banana', 'papaya', 'avocado', 'coconut', 'pineapple', 'guava', 'ginger', 'nutmeg', 'okra',
           'rosemary', 'jackfruit', 'turmeric', 'mango', 'curry leaf', 'date palm', 'coriander',
           'carambola']
all_fv_info = []
item = {}
is_fresh_login = True


def get_fruit_and_veg_info():
    # access the fruit and veg API and get the required info
    # get the other name, image url and health info

    for item in fv_list:
        param = {"tfvitem": item}

        response = requests.get(API_path, param)
        data = response.json()
        # print(data)
        other_name = data['results'][0]['othname']
        img_url = data['results'][0]['imageurl']
        health_info = data['results'][0]['health']
        each_item = {'name': item, 'other_name': other_name, 'img_url': img_url, 'health_info': health_info}
        all_fv_info.append(each_item)


get_fruit_and_veg_info()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    # go to home-page
    # call get_fruit_and_veg_info function

    # check if its a fresh login then clear cookies and delete previous stored session
    global is_fresh_login
    if is_fresh_login:
        logout_user()
        is_fresh_login = False
        return redirect(url_for('home'))

    global item
    # check if item is empty then go to home-page else go to the blog page (i.e. 'secrets')
    if item == {}:
        print(current_user)
        print(current_user.is_authenticated)
        return render_template('home.html', fvlist=all_fv_info, logged_in=current_user.is_authenticated)
    elif item != {} and current_user.is_authenticated is True:
        return redirect(url_for('secrets', item=item))
    elif item != {} and current_user.is_authenticated is False:
        return redirect(url_for('home', item=item))


@app.route('/signup', methods=["GET", "POST"])
def signup():
    global item
    # check if query strings were passed as argument through the URL
    if not request.args.get('name') is None:
        # check if the user has already been logged in
        img_url = request.args.get('img_url')
        name = request.args.get('name')
        other_name = request.args.get('other_name')
        health_info = request.args.get('health_info')
        item = {'img_url': img_url, 'name': name, 'other_name': other_name, 'health_info': health_info}

    if request.method == 'POST':

        if User.query.filter_by(email=request.form.get('email')).first():
            # user already exists
            flash("You have already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(request.form['password'], 'pbkdf2:sha256', 8)
        name = request.form['name']
        email = request.form['email']
        password = hash_and_salted_password
        new_user = User(name=name, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()

        # login and authenticate user after adding details to database.
        login_user(new_user)

        return redirect(url_for('home'))

    # check if the user has already logged in then go to blog page else go to home page
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        return render_template('signup.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # find user by email entered.
        user = User.query.filter_by(email=email).first()
        # Email doesnt exist
        if not user:
            flash('That email does not exist, please try again.')
            return redirect(url_for('login'))
        # password incorrect
        elif not check_password_hash(user.password, password):
            flash('password incorrect, please try again.')
            return redirect(url_for('login'))
        # Email exists and password correct
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/search', methods=["GET", "POST"])
def search():
    if current_user.is_authenticated is True:
        name=request.form['name']
        if name != '':
            for item in all_fv_info:
                if item['name'].lower() == name.lower():
                    return render_template("secrets.html", item=item, logged_in=True)
                else:
                    pass
            # redirect to home page (with a flash message) if the name is not found
        flash('Item not found!.')
        return redirect(url_for('home'))
    else:
        flash('signup or login to use the search bar.')
        return redirect(url_for('signup'))



@app.route('/secrets')
@login_required
def secrets():
    global item
    received_item = item
    item = {}

    return render_template("secrets.html", item=received_item, logged_in=True)


if __name__ == "__main__":
    app.run(debug=True)
