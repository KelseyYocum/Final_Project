from flask import Flask, render_template, redirect, request, g, session, url_for, flash
from model import session as DB, User, Series, Episode, requests, pq, add_series
from flask.ext.login import LoginManager, login_required, login_user, current_user
from flaskext.markdown import Markdown
import config
import forms
import model



app = Flask(__name__)
app.config.from_object(config)

# Stuff to make login easier
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# End login stuff

# Adding markdown capability to the app
Markdown(app)

# @app.route("/")
# def index():
#     posts = Post.query.all()
#    return render_template("index.html", posts=posts)

# @app.route("/post/<int:id>")
# def view_post(id):
#     post = Post.query.get(id)
#     return render_template("post.html", post=post)

# @app.route("/post/new")
# @login_required
# def new_post():
#     return render_template("new_post.html")

# @app.route("/post/new", methods=["POST"])
# @login_required
# def create_post():
#     form = forms.NewPostForm(request.form)
#     if not form.validate():
#         flash("Error, all fields are required")
#         return render_template("new_post.html")

#     post = Post(title=form.title.data, body=form.body.data)
#     current_user.posts.append(post) 
    
#     model.session.commit()
#     model.session.refresh(post)

#     return redirect(url_for("view_post", id=post.id))



@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def authenticate():
    form = forms.LoginForm(request.form)
    if not form.validate():
        flash("Incorrect username or password") 
        return render_template("login.html")

    email = form.email.data
    password = form.password.data

    user = User.query.filter_by(email=email).first()

    if not user or not user.authenticate(password):
        flash("Incorrect username or password") 
        return render_template("login.html")

    login_user(user)
    return redirect(request.args.get("next", url_for("index")))


@app.route("/")
def index():
    series = Series.query.all()
    #current_user = current_user
    return render_template("index.html")

@app.route("/search")
def search_page():
    return render_template("search.html")


@app.route("/search", methods = ["POST"])
def search_results():
    search_input = request.form.get("search")

    r = requests.get('http://thetvdb.com/api/GetSeries.php?seriesname='+search_input)
    xml_doc = r.text
    xml_doc = xml_doc.encode('utf-8')
    pyQ = pq(xml_doc, parser = 'xml')

    series_search_results = pyQ('Series')
    series_list = []
    for s in series_search_results:
        single_series_id =(pyQ(s).find('id').text())
        single_series = model.parse_series(single_series_id)
        series_list.append(single_series)

    
    return render_template("search.html", series_list = series_list, 
                                            search_input=search_input) 

        # where series_list is a list of series in pyQuery xml


@app.route("/series/<external_series_id>")
def display_series_info(external_series_id):

    #is series already in database?
    count = DB.query(Series).filter_by(external_id = external_series_id).count()

    if count == 0:
        add_series(external_series_id)
    series = DB.query(Series).filter_by(external_id = external_series_id).one()
    banner = requests.get(series.banner).content

    return render_template("series_page.html", series = series, current_user=current_user) # where series is a db object


@app.route("/series-forms")
def series_forms():
    return render_template("series_forms.html")

@app.route("/add-user-series", methods = ["POST"])
def add_to_user_series_table():
    user_id = int(request.form.get("user_id"))
    series_id = int(request.form.get("series_id"))
    state = request.form.get("state")

    new_user_series = model.UserSeries(user_id=user_id, series_id=series_id, state=state)
    DB.add(new_user_series)
    DB.commit()
    return "success!"


@app.route("/add-fav-series", methods = ["POST"])
def add_to_favorite_series_table():
    user_id = int(request.form.get("user_id"))
    series_id = int(request.form.get("series_id"))

    new_fav = model.Favorite(user_id=user_id, series_id=series_id)
    DB.add(new_fav)
    DB.commit()
    return "success!"

# so you need to have a this fake form (series_forms.html) made for the jQuery to work?
# how do you get the current user printed in the header
    # how to use current user

if __name__ == "__main__":
    app.run(debug=True)
