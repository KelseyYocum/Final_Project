import config
import bcrypt
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text

from sqlalchemy.orm import sessionmaker, scoped_session, relationship, backref

from flask.ext.login import UserMixin

from pyquery import PyQuery as pq
from lxml import etree
import urllib
import requests

engine = create_engine(config.DB_URI, echo=False) 
session = scoped_session(sessionmaker(bind=engine,
                         autocommit = False,
                         autoflush = False))

Base = declarative_base()
Base.query = session.query_property()

class User(Base, UserMixin):
    __tablename__ = "users" 
    id = Column(Integer, primary_key=True)
    email = Column(String(64), nullable=False)
    password = Column(String(64), nullable=False)
    salt = Column(String(64), nullable=False)

    #friends


    def set_password(self, password):
        self.salt = bcrypt.gensalt()
        password = password.encode("utf-8")
        self.password = bcrypt.hashpw(password, self.salt)

    def authenticate(self, password):
        password = password.encode("utf-8")
        return bcrypt.hashpw(password, self.salt.encode("utf-8")) == self.password

# class Post(Base):
#     __tablename__ = "posts"
    
#     id = Column(Integer, primary_key=True)
#     title = Column(String(64), nullable=False)
#     body = Column(Text, nullable=False)
#     created_at = Column(DateTime, nullable=False, default=datetime.now)
#     posted_at = Column(DateTime, nullable=True, default=None)
#     user_id = Column(Integer, ForeignKey("users.id"))

#     user = relationship("User")


class Series(Base):
    __tablename__ = "series"
    id = Column(Integer, primary_key=True)
    external_id = Column(Integer, nullable = True)

    #first_aired = Column(String(64), nullable = True) 
    # airs_day_of_week = Column(String(10), nullable = True)
    # airs_time = Column(String(64), nullable = True)
    # status = Column(String(12), nullable = True)

    title = Column(String(64), nullable = True)
    overview = Column(Text, nullable = True)
    genre = Column(String(64), nullable = True)
    
    # banner = Column(String, nullable = True)
    
    episodes = relationship("Episode", backref = "series")
    
    

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True)
    external_id = Column(Integer, nullable = True)
    
    ep_num = Column(Integer(64), nullable = True)
    season_num = Column(Integer(64),nullable = True)

    #first_aired = Column(String(64), nullable = True) 

    title = Column(String(64), nullable = True)
    overview = Column(Text, nullable = True)
    
    # image = Column(String, nullable = True)

    series_id = Column(Integer, ForeignKey('series.id'))

    #backref with .series
    

# class Friendships(Base):
#     pass


################ The Lists ####################

class CurrentlyWatching(Base):
    __tablename__ = "currently_watching"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id')) #local series id

    user = relationship("User", backref = "currently_watching")
    series = relationship("Series", backref = "currently_watching")

    #user.currently_watching -->list of currently watching objs

class Watched(Base):
    __tablename__ = "watched"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id')) #local series id

    user = relationship("User", backref = "watched")
    series = relationship("Series", backref = "watched")

    #user.watched -->list of previously watched objs

class ToWatch(Base):
    __tablename__ = "to_watch"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id')) #local series id

    user = relationship("User", backref = "to_watch")
    series = relationship("Series", backref = "to_watch")

    #user.to_watch -->list of to_watch objs

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id')) #local series id

    user = relationship("User", backref = "favorites")
    series = relationship("Series", backref = "favorites")

    # user.favorites -->list of favorites objs
    # currently set up for only favorite series, not favorite eps or seasons



################## Social Interactions #############################

# class Friend(Base):
#     __tablename__ = "friends"


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id'))
    ep_id = Column(Integer, ForeignKey('episodes.id')) #local ep id
    value = Column(Integer, nullable = False)

    user = relationship("User", backref = "ratings")
    episode = relationship("Episode", backref = "ratings")

    # user.ratings -->list of ratings objs
    # currently set up for rating only episodes, not series or seasons


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id')) #the author
    ep_id = Column(Integer, ForeignKey('episodes.id')) #local ep id
    body = Column(Text, nullable = False)
    #date = Column(DateTime, nullable = False)

    user = relationship("User", backref = "reviews")
    episode = relationship("Episode", backref = "reviews")

    # user.reviews -->list of review objs
    # currently set up for reviewing only episodes, not series or seasons


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id')) #comment author
    review_id = Column(Integer, ForeignKey('reviews.id')) 
    body = Column(Text, nullable = False)
    #date = Column(DateTime, nullable = False)

    user = relationship("User", backref = "comments")
    review = relationship("Review", backref = "comments")

    # user.comments -->list of commment objs
    # currently set up for comment on only reviews, not feed stuff (?) 


#recommendations from friends, not an engine
class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key = True)

    #user who is giving the recommendation
    recommender_id = Column(Integer, ForeignKey('users.id'))

    #user recieving the recommendation
    recommendee_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id')) #local series id
    body = Column(Text, nullable = False)
    #date = Column(DateTime, nullable = False)

    # recommender = relationship("User", foreign_keys =[recommender_id], backref = "recommendations")
    # recommendee = relationship("User", foreign_keys =[recommendee_id], backref = "recommendations")

    recommender = relationship("User", foreign_keys =[recommender_id])
    recommendee = relationship("User", foreign_keys =[recommendee_id])

    series = relationship("Series", backref = "recommendations")

    # user.recommendations -->list of recommendation objs
    # can only recommend series


# class Friendship(Base):
#     __tablename__ = "friendships"
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('users.id'))
#     friend_id = Column(Integer, ForeignKey('users.id'))

#     user = relationship("User", backref = "recommendations")
#     friend = relationship("User", backref = "recommendations")


################# Table Functions #####################

def parse_series(external_series_id):
    r = requests.get('http://thetvdb.com/data/series/'+ external_series_id +'/all')
    xml_doc = r.text
    xml_doc = xml_doc.encode("utf-8")

    pyQ = pq(xml_doc, parser = "xml")
    return pyQ

#add series to local db from api db given an api db series id
def add_series(external_series_id):
    data = parse_series(external_series_id)



def create_tables():
    Base.metadata.create_all(engine)
    u = User(email="test@test.com")
    u.set_password("unicorn")
    session.add(u)

    u2 = User(email="test2@test.com")
    u2.set_password("bubbles")
    session.add(u2)

    # p = Post(title="This is a test post", body="This is the body of a test post.")
    # u.posts.append(p)
    s = Series(external_id=123, title = "Broadchurch", overview = "lorem ipsum", genre = "Drama | Mystery")
    session.add(s)

    s2 = Series(external_id=223, title = "Doctor Who", overview = "lorem ipsum", genre = "SciFi | Adventure")
    session.add(s2)

    e = Episode(external_id= 456, title = "First Ep Title", ep_num = 1, season_num = 1, overview = "more lorem ipsum", series_id = "1")
    session.add(e)

    currently_w = CurrentlyWatching(user_id = 1, series_id = 1)
    currently_w2 = CurrentlyWatching(user_id = 1, series_id = 2)
    session.add(currently_w)
    session.add(currently_w2)

    rating = Rating(user_id = 1, ep_id = 2, value = 5)
    session.add(rating)

    review = Review(user_id = 1, ep_id = 1, body = "commodo libero eget nisl rutrum eleifend. Nulla dapibus euismod pulvinar. Nulla nec turpis vehicula odio malesuada commodo. Suspendisse potenti. Nullam sagittis, est in tempus fermentum, odio neque volutpat erat, et congue nisi leo vel dolor. Aliquam semper porta risus, id ullamcorper est commodo eu. Sed scelerisque volutpat lacus, sit amet posuere sapien aliquam a. Donec consectetur turpis rutrum, porta lectus id, rutrum felis.")
    session.add(review)

    comment = Comment(user_id = 1, review_id = 1, body = "sweet review")
    session.add(comment)

    rec = Recommendation(recommender_id = 2, recommendee_id = 1, series_id = 2, body = "blah blah blah")
    session.add(rec)

    session.commit()

if __name__ == "__main__":
    create_tables()
