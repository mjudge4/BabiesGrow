# Provides objects and variables to manipulate the project runtime environment

import sys

# Object relational mapping
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime

# To create instance of the class called declarative base to import SQL Alchemy Features
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

DATA_BACKEND = 'cloudsql'
CLOUDSQL_USER = 'marc'
CLOUDSQL_PASSWORD = 'password'
CLOUDSQL_DATABASE = 'offerings'

CLOUDSQL_CONNECTION_NAME = 'pycharm-194111:us-central1:babiesgrow'

# Create instance
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))





class Offering(Base):
    __tablename__ = 'offering'

    id = Column(Integer, primary_key=True )
    title = Column(String(300), nullable=False)
    date = Column(String(300), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    files = relationship('File', passive_deletes=True)

    @property
    def serialize(self):
        #Return objects in serializable form
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date,

        }



class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    tag_name = Column(String(300), nullable=False)
    offering_id = Column(Integer, ForeignKey('offering.id'))
    offering = relationship(Offering)

    @property
    def serialize(self):
        # Return objects in serializable form
        return {
            'id': self.id,
            'name': self.name,

        }


class Comment(Base):
    __tablename__ = 'comment'

    id = Column(Integer, primary_key=True)
    body = Column(String(1000), nullable=False)
    offering_id = Column(Integer, ForeignKey('offering.id'))
    offering = relationship(Offering)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # Return objects in serializable form
        return {
            'id': self.id,
            'body': self.body,

        }

class File(Base):
    __tablename__ = 'file'

    id = Column(Integer, primary_key=True)
    image = Column(String(250))
    offering_id = Column(Integer, ForeignKey('offering.id', ondelete='CASCADE'))
    offering = relationship(Offering)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)



    @property
    def serialize(self):
        # Return objects in serializable form
        return {
            'id': self.id,
            'image': self.image,

        }



# Engine instance with a mysql database
engine = create_engine('mysql+pymysql://marc:password@127.0.0.1:8000/offerings')

# Goes into database and creates the tables
Base.metadata.create_all(engine)