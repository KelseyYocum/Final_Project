import config
import bcrypt
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text

from sqlalchemy.orm import sessionmaker, scoped_session, relationship, backref

from flask.ext.login import UserMixin

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

    #posts = relationship("Post", uselist=True)

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
    extnernal_id = Column(Integer, nullable = True)
    title = Column(String(64), nullable = True)
    overview = Column(Text, nullable = True)
    banner = Column(String, nullable = True)
    #first_aired = Column(String(64), nullable = True) 
    genre = Column(String(64), nullable = True)
    
    episodes = relationship("Episode")
    
    

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True)
    extnernal_id = Column(Integer, nullable = True)
    title = Column(String(64), nullable = True)
    ep_num = Column(Integer(64), nullable = True)
    season_num = Column(Integer(64),nullable = True)
    overview = Column(Text, nullable = True)
    #first_aired = Column(String(64), nullable = True) 
    image = Column(String, nullable = True)

    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship("Series")






def create_tables():
    Base.metadata.create_all(engine)
    u = User(email="test@test.com")
    u.set_password("unicorn")
    session.add(u)

    # p = Post(title="This is a test post", body="This is the body of a test post.")
    # u.posts.append(p)
    s = Series(extnernal_id=123, title = "Broadchurch", overview = "lorem ipsum", genre = "Drama | Mystery")
    session.add(s)

    e = Episode(extnernal_id= 456, title = "Frist Ep Title", ep_num = 1, season_num = 1, overview = "more lorem ipsum", series_id = "1")
    session.add(e)

    session.commit()

if __name__ == "__main__":
    create_tables()
