from flask import Flask, render_template, redirect, request, g, session, url_for, flash, jsonify
from model import session as DB, User, Series, Episode, UserSeries, requests, pq, add_series
from flask.ext.login import LoginManager, login_required, login_user, current_user
from flaskext.markdown import Markdown
import config
import forms
import model
import json
import operator



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

def series_to_dict(series):
    return {
        "title" : series.title,
        "external_id" : series.external_id,
        "poster" : series.poster
    }


# where series_list is a list of seris objects
# where series_tuple_list is a list of tuples containg 6 series dictionaries each. 
# sets of six to account for bootstrap rows and columns 
# (6, 2-column series entries per row)
# The series dicts each have external_id, poster and title keys

def series_tuple_list(series_list):
    series_list = [series_to_dict(s) for s in series_list]
    # make it a len mod 6 length by appending zeros (so don't cut off any series)
    for i in range(6-(len(series_list)%6)):
        series_list.append(0)

    series_tuple_list=zip(*[iter(series_list)]*6)

    return series_tuple_list


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

        external_id = int(single_series('id').text())
        title = single_series('SeriesName').text()

        if single_series('poster').text() != '':
            poster = "http://thetvdb.com/banners/"+single_series('poster').text()
            series_obj = model.Series(external_id=external_id, poster=poster, title=title) 
            series_list.append(series_obj)
        
    series_list=series_tuple_list(series_list)
    print series_list
    
    return render_template("search.html", series_list = series_list, 
                                            search_input=search_input) 
  

# need a def that turns a tv series into a list of dictionaries
#eps =session.query(Episode).filter_by(series_id=4).order_by(Episode.season_num).all()
#seasons.keys().sort()
#dictionary of seasons {1:[ep, ep, ep], 2:[ep,ep,ep]}
#{1:{1:ep, 2:ep, 3:ep}, 2:{1:ep, 2:ep, 3:ep}}

@app.route("/series/<external_series_id>")
def display_series_info(external_series_id):

    #is series already in database?
    count = DB.query(Series).filter_by(external_id = external_series_id).count()

    if count == 0:
        add_series(external_series_id)
    series = DB.query(Series).filter_by(external_id = external_series_id).one()
    banner = requests.get(series.banner).content

    count2 = DB.query(UserSeries).filter_by(
                                    series_id=series.id, 
                                    user_id=current_user.id).count()

    if count2 != 0:
        state = DB.query(UserSeries).filter_by(
                                        series_id=series.id, 
                                        user_id=current_user.id).one().state
    else:
        state = '';

    favorite_series = DB.query(model.Favorite).filter_by(series_id=series.id, user_id=current_user.id).first()

    if favorite_series != None:
        favorite = True
    else:
        favorite = False

    
    # all episodes of series organized by season
    #{1:[ep, ep, ep], 2:[ep,ep,ep], ...}

    eps_list = DB.query(Episode).filter_by(series_id=series.id).order_by(Episode.season_num).all()
    season_dict = {}
   

    for e in eps_list:
        if season_dict.get(e.season_num) == None:
            season_dict[e.season_num]=[e]
        else:
            season_dict[e.season_num].append(e)

        # count3=DB.query(model.WatchedEpisode).filter_by(episode_id = e.id).count()
        # if count3 != 0:
        #     watched_ep_ids.append(e.id)

    # in each episode list per season key, sort by episode number
    for key, val in season_dict.iteritems():
        val.sort(key=operator.attrgetter("ep_num"))


    rating_count = DB.query(model.Rating).filter_by(series_id=series.id, user_id=current_user.id).count()
    if rating_count != 0:
        rating_value = DB.query(model.Rating).filter_by(series_id=series.id, user_id=current_user.id).one().value
    else:
        rating_value = 0


    #percent_watched = round(float((len(watched_ep_ids))/float(len(eps_list)))*100, 1)
    watched_count = DB.query(model.WatchedEpisode).\
        join(model.WatchedEpisode.episode).\
        filter(model.Episode.series_id == series.id).\
        filter(model.WatchedEpisode.user_id == current_user.id).count()

    watched_eps = DB.query(model.WatchedEpisode).\
        join(model.WatchedEpisode.episode).\
        filter(model.Episode.series_id == series.id).\
        filter(model.WatchedEpisode.user_id == current_user.id).all()

    watched_ep_ids=[]

    for ep in watched_eps:
        watched_ep_ids.append(ep.episode_id)

    print "WATCHED EP IDS", watched_ep_ids

    
    percent_watched = round(100 * float(watched_count)/float(len(eps_list)), 1)


    return render_template("series_page.html", state=state, 
                                            series = series, 
                                            current_user=current_user,
                                            season_dict=season_dict,
                                            watched_ep_ids=watched_ep_ids,
                                            rating=rating_value,
                                            favorite=favorite,
                                            percent_watched=percent_watched

                                            
                                            ) # where series is a db object, 
                                            # season_dict keys are season numbers, values are lists of ep objs



@app.route("/series/<series_id>/episode/<episode_id>")
def display_episode_info(series_id, episode_id):

    episode = DB.query(Episode).filter_by(id = episode_id).one()
    series = DB.query(Series).filter_by(id=series_id).one()

    return render_template("episode_page.html", episode=episode, series=series)



@app.route("/my-shows")
def display_my_shows():
    return render_template("my_shows.html")

@app.route("/my-shows/watching")
def display_watching_shows():
    #trying to get a list of series that the current_user is watching
    watching_list = DB.query(UserSeries).filter_by(user_id=current_user.id, state="watching").all()
    watching_series_list = []
    for user_series in watching_list:
        watching_series_list.append(user_series.series)
    watching_series_list = series_tuple_list(watching_series_list)
    return json.dumps(watching_series_list)


@app.route("/my-shows/watched")
def display_watched_shows():
    #trying to get a list of series that the current_user is watching
    watched_list = DB.query(UserSeries).filter_by(user_id=current_user.id, state="watched").all()
    watched_series_list = []
    for user_series in watched_list:
        watched_series_list.append(user_series.series)
    watched_series_list = series_tuple_list(watched_series_list)
    return json.dumps(watched_series_list)

@app.route("/my-shows/to-watch")
def display_to_watch_shows():
    #trying to get a list of series that the current_user is watching
    to_watch_list = DB.query(UserSeries).filter_by(user_id=current_user.id, state="to-watch").all()
    to_watch_series_list = []
    for user_series in to_watch_list:
        to_watch_series_list.append(user_series.series)
    to_watch_series_list = series_tuple_list(to_watch_series_list)
    return json.dumps(to_watch_series_list)


@app.route("/my-shows/favorites")
def display_favorite_shows():
    #trying to get a list of series that the current_user is watching
    favorites_list = current_user.favorites
    fav_series_list = []
    for fav in favorites_list:
        fav_series_list.append(fav.series)
    fav_series_list = series_tuple_list(fav_series_list)
    return json.dumps(fav_series_list)



@app.route("/series-forms")
def series_forms():
    return render_template("series_forms.html")

@app.route("/add-user-series", methods = ["POST"])
def add_to_user_series_table():
    user_id = int(request.form.get("user_id"))
    series_id = int(request.form.get("series_id"))
    state = request.form.get("state")

    new_user_series = model.UserSeries(user_id=user_id, series_id=series_id, state=state)
    count = DB.query(UserSeries).filter_by(series_id=series_id, 
                                        user_id=user_id).count()
    if count == 0:
        DB.add(new_user_series)
        DB.commit()
        print "added new user series!"
    else: 
        db_duplicate = DB.query(UserSeries).filter_by(series_id=series_id, 
                                                        user_id=user_id).one()
        if db_duplicate.state != state:
            db_duplicate.state = state
            DB.add(db_duplicate)
            DB.commit()
            print "Changed to a new state!"
    return "success!"


@app.route("/add-fav-series", methods = ["POST"])
def add_to_favorites():
    user_id = int(request.form.get("user_id"))
    series_id = int(request.form.get("series_id"))

    new_fav = model.Favorite(user_id=user_id, series_id=series_id)
    count = DB.query(model.Favorite).filter_by(series_id=series_id, 
                                        user_id=user_id).count()
    if count == 0:
        DB.add(new_fav)
        DB.commit()
        print "new fav added!"
    return "success!"

@app.route("/remove-fav-series", methods = ["POST"])
def remove_from_favorites():
    user_id = int(request.form.get("user_id"))
    series_id = int(request.form.get("series_id"))

    fav = DB.query(model.Favorite).filter_by(series_id = series_id, 
                                        user_id=user_id).one()
    DB.delete(fav)
    DB.commit()

    return "Deleted fav!"



@app.route("/update-watched-episode", methods = ["POST"])
def update_watched_episodes():
    user_id = int(request.form.get("user_id"))
    episode_id = int(request.form.get("episode_id"))
    status = request.form.get("status")
    print status
    
    if status == "true":
        watched_episode = model.WatchedEpisode(user_id=user_id, episode_id=episode_id)
        DB.add(watched_episode)
    else:
        watched_episode=DB.query(model.WatchedEpisode).filter_by(user_id=user_id, episode_id=episode_id).one()
        DB.delete(watched_episode)

    DB.commit()
    series = DB.query(Series).filter(Series.episodes.any(Episode.id == episode_id)).one()

    eps_list = DB.query(Episode).filter_by(series_id=series.id).order_by(Episode.season_num).all()
    season_dict = {}
    watched_ep_ids =[]

    watched_count = DB.query(model.WatchedEpisode).\
        join(model.WatchedEpisode.episode).\
        filter(model.Episode.series_id == series.id).\
        filter(model.WatchedEpisode.user_id == user_id).count()

    
    pct = round(100 * float(watched_count)/float(len(eps_list)), 1)

    response = {
        'success': True,
        'completion_percentage': pct,
    }

    return jsonify(response)


@app.route("/series/rating", methods = ["POST"])
def update_series_rating():
    value = request.form.get("value")
    series_id = request.form.get("series_id")
    user_id = request.form.get("user_id")

    count = DB.query(model.Rating).filter_by(user_id=user_id, series_id=series_id).count()
    user_series_count = DB.query(UserSeries).filter_by(user_id=user_id, series_id=series_id).count()

    if count == 0:
        #can only rate if you've added it to one of your watched lists
        if user_series_count != 0:
            new_rating = model.Rating(series_id=series_id, user_id=user_id, value=value)
            DB.add(new_rating)
            DB.commit()
    else:
        rating = DB.query(model.Rating).filter_by(user_id=user_id, series_id=series_id).one()
        rating.value = value
        DB.add(rating)
        DB.commit()

    return "successfully updated rating!"




if __name__ == "__main__":
    app.run(debug=True)
