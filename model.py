# import docopt
# 


import config
import bcrypt
from datetime import datetime
import string

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text

from sqlalchemy.orm import sessionmaker, scoped_session, relationship, backref
from sqlalchemy.schema import Table

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
    username = Column(String(64), nullable=False)
    salt = Column(String(64), nullable=False)

    friends = relationship('User', secondary='friendship', 
        primaryjoin='User.id == friendship.c.from_user_id',
        secondaryjoin='friendship.c.to_user_id == User.id')


    def set_password(self, password):
        self.salt = bcrypt.gensalt()
        password = password.encode("utf-8")
        self.password = bcrypt.hashpw(password, self.salt)

    def authenticate(self, password):
        password = password.encode("utf-8")
        return bcrypt.hashpw(password, self.salt.encode("utf-8")) == self.password

    def add_friend(self, *friends):
        for f in friends:
            self.friends.append(f)
            f.friends.append(self)


class Series(Base):
    __tablename__ = "series"
    id = Column(Integer, primary_key=True)
    external_id = Column(Integer, nullable = True)

    first_aired = Column(DateTime, nullable = True) 
    airs_day_of_week = Column(String(10), nullable = True)
    airs_time = Column(DateTime, nullable = True)
    status = Column(String(12), nullable = True)
    title = Column(String(64), nullable = True)
    overview = Column(Text, nullable = True)
    genre = Column(String(64), nullable = True)
    
    banner = Column(String(64), nullable = False)
    poster = Column(String(64), nullable = False)
    fanart = Column(String(64), nullable = False)
    
    episodes = relationship("Episode", backref = "series")
    
    
class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True)
    external_id = Column(Integer, nullable = True)
    
    ep_num = Column(Integer(64), nullable = True)
    season_num = Column(Integer(64),nullable = True)

    first_aired = Column(DateTime, nullable = True) 

    title = Column(String(64), nullable = True)
    overview = Column(Text, nullable = True)
    
    image = Column(String(64), nullable = True)

    series_id = Column(Integer, ForeignKey('series.id'))


################ The Lists ####################


class UserSeries(Base):
    __tablename__ = "user_series"
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id'))  # Local series id
    state = Column(String(65), nullable = False)   # Set to watched, to-watch, watching

    user = relationship("User", backref = "user_series")
    series = relationship("Series", backref = "user_series")

class WatchedEpisode(Base):
    __tablename__ = "watched_episodes"
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('users.id'))
    episode_id = Column(Integer, ForeignKey('episodes.id')) 

    user = relationship("User", backref = "watched_episodes")
    episode = relationship("Episode", backref = "watched_episodes")

# currently set up for only favorite series, not favorite eps or seasons
class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id')) #local series id

    user = relationship("User", backref = "favorites")
    series = relationship("Series", backref = "favorites")


################## Social Interactions #############################


# currently set up for rating only series, not episodes or seasons
class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id')) #local ep id
    value = Column(Integer, nullable = False)

    user = relationship("User", backref = "ratings")
    series = relationship("Series", backref = "ratings")

# currently set up for reviewing only episodes, not series or seasons
class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id')) #the author
    ep_id = Column(Integer, ForeignKey('episodes.id')) #local ep id
    body = Column(Text, nullable = False)
    #date = Column(DateTime, nullable = True)

    user = relationship("User", backref = "reviews")
    episode = relationship("Episode", backref = "reviews")

    
class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key = True)

    user_id = Column(Integer, ForeignKey('users.id')) #comment author
    review_id = Column(Integer, ForeignKey('reviews.id')) 
    body = Column(Text, nullable = False)
    #date = Column(DateTime, nullable = True)

    user = relationship("User", backref = "comments")
    review = relationship("Review", backref = "comments")


# recommendations from friends, not an engine
# user.recommendations_given -->list of recommendation objs that user has given
# user.recommendations_recv -->list of recommendation objs that user has recieved
# can only recommend series
class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key = True)

    #user who is giving the recommendation
    recommender_id = Column(Integer, ForeignKey('users.id'))

    #user recieving the recommendation
    recommendee_id = Column(Integer, ForeignKey('users.id'))
    series_id = Column(Integer, ForeignKey('series.id')) #local series id
    body = Column(Text, nullable = False)
    #date = Column(DateTime, nullable = True)

    recommender = relationship("User", foreign_keys =[recommender_id], backref = "recommendations_given")
    recommendee = relationship("User", foreign_keys =[recommendee_id], backref = "recommendations_recv")

    series = relationship("Series", backref = "recommendations")

    
Table('friendship', Base.metadata,
    Column('from_user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('to_user_id', Integer, ForeignKey('users.id'), primary_key=True))


################## Table Functions #####################


# Uses request and pyquery to retrieve and parse xml from tv api
# pyquery allows you to make jquery queries on xml docs
def parse_series(external_series_id):
    r = requests.get('http://thetvdb.com/data/series/'+ external_series_id)
    xml_doc = r.text
    xml_doc = xml_doc.encode("utf-8")

    pyQ = pq(xml_doc, parser = "xml")
    return pyQ

def parse_series_with_eps(external_series_id):
    r = requests.get('http://thetvdb.com/data/series/'+ external_series_id+'/all/')
    xml_doc = r.text
    xml_doc = xml_doc.encode("utf-8")

    pyQ = pq(xml_doc, parser = "xml")
    return pyQ

def parse_episode(external_series_id, season_num, ep_num):
    r = requests.get('http://thetvdb.com/data/series/'+external_series_id+'/default/'+season_num+'/'+ep_num)
    xml_doc = r.text
    xml_doc = xml_doc.encode("utf-8")

    pyQ = pq(xml_doc, parser = "xml")
    return pyQ


def add_episodes(external_series_id):
    pyQ = parse_series_with_eps(external_series_id)
    episodes = pyQ('Episode')


    for e in episodes:
        season_num = int(pyQ(e).find('SeasonNumber').text())

        #not adding season 0 episodes because those refer to releases like interviews or making-ofs, not actual episodes
        if season_num != 0:
            external_id = int(pyQ(e).find('id').text())
            ep_num = int(pyQ(e).find('EpisodeNumber').text())
            
            date_str=pyQ(e).find('FirstAired').text()
            if date_str != '':
                first_aired = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                first_aired = None

            title = pyQ(e).find('EpisodeName').text()
            overview = pyQ(e).find('Overview').text()
            image = "http://thetvdb.com/banners/"+pyQ(e).find('filename').text()

            series = session.query(Series).filter_by(external_id = external_series_id).one()
            series_id = series.id

            ep = Episode(external_id = external_id, 
                            ep_num = ep_num, 
                            season_num = season_num, 
                            first_aired = first_aired, 
                            title = title, 
                            overview=overview, 
                            image = image, 
                            series_id = series_id)
            session.add(ep)

    session.commit()


# Add series to local db from api db given an api db series id
def add_series(external_series_id):
    pyQ = parse_series(external_series_id)
    external_id = int(pyQ('id').text())

    date_str=pyQ('FirstAired').text()
    if date_str != '':
        first_aired = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        first_aired = None
  
    time_str = pyQ('Airs_Time').text()
    if time_str != '':
        airs_time = datetime.strptime(time_str, '%I:%M %p')
    else:
        airs_time =None
 
    airs_day_of_week = pyQ('Airs_DayOfWeek').text()
    status = pyQ('Status').text()
    title = pyQ('SeriesName').text()
    overview = pyQ('Overview').text()

    genre_original = pyQ('Genre').text()
    genre = genre_original.strip('|')
    genre=string.replace(genre, '|', ', ')
    
    banner = "http://thetvdb.com/banners/"+pyQ('banner').text()
    poster = "http://thetvdb.com/banners/"+pyQ('poster').text()
    fanart = "http://thetvdb.com/banners/"+pyQ('fanart').text()

    s = Series(external_id = external_id, 
                first_aired = first_aired, 
                airs_day_of_week = airs_day_of_week, 
                airs_time = airs_time, 
                status = status, 
                title = title, 
                overview=overview, 
                genre = genre, 
                banner = banner, 
                poster= poster, 
                fanart = fanart)
    
    session.add(s)
    session.commit()
    
    #add eps of the series to DB as well
    add_episodes(external_series_id)


###########################################################


def create_tables():
    Base.metadata.create_all(engine)

    u = User(email="test@test.com", username='Jill')
    u.set_password("bubbles")
    session.add(u)


    u2 = User(email="test2@test.com", username='Paul')
    u2.set_password("unicorn")
    u2.add_friend(u)
    session.add(u2)

    u3 = User(email='test3@test.com', username='Sarah')
    u3.set_password('password')
    u3.add_friend(u, u2)
    session.add(u3)
  
    session.commit()

if __name__ == "__main__":
    create_tables()
