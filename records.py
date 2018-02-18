from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Offering, Tag, Comment

engine = create_engine('mysql://root:password@localhost/mynewdatabase')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Superman", email="superman@krypton.com",
             picture='http://entertainment.ie//images_content/rectangle/620x372/christopher-reeve-superman.jpg')
session.add(User1)
session.commit()

offering1 = Offering(user_id=1, title="Godchild", date="October")
session.add(offering1)
session.commit()

tag1 = Tag(tag_name="Babygrow", offering=offering1)
session.add(tag1)
session.commit()

tag2 = Tag(tag_name="Novelty", offering=offering1)
session.add(tag2)
session.commit()

comment1 = Comment(user_id=1, body="That looks great", offering=offering1)
session.add(comment1)
session.commit()


offering2 = Offering(user_id=1, title="Super", date="October")
session.add(offering2)
session.commit()

comment2 = Comment(user_id=1, body="Fabulous", offering=offering2)
session.add(comment2)
session.commit()

print "Offerings added"