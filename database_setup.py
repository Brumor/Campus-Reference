import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()


class Category(Base):
	
	__tablename__ = 'category'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(200), nullable= False)
	is_verified = Column(Boolean)


class Subcategory(Base):
	
	__tablename__ = 'subcategory'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	is_verified = Column(Boolean)
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category)
	

class User(Base):
	
	__tablename__ = 'user'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(30), nullable=False)
	email = Column(String(30), nullable=False)
	isCertified = Column(Boolean, nullable=False)
	picture = Column(String)


class Chapter(Base):
	
	__tablename__ = 'article'
		
	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	content = Column(String, nullable=False)
	creation_date = Column(Date, nullable=False)
	last_update = Column(Date, nullable=False)
	subcategory_id = Column(Integer, ForeignKey('subcategory.id'))
	subcategory = relationship(Subcategory)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	user_name = Column(String)
	user_picture = Column(String)
	is_verified = Column(Boolean)
	
class PersonalChapter(Base):
	
	__tablename__ = 'personalarticle'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	content = Column(String, nullable=False)
	creation_date = Column(Date, nullable=False)
	last_update = Column(Date, nullable=False)
	article_id = Column(Integer, ForeignKey('article.id'))
	article = relationship(Chapter)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	
	
class Discussion(Base):
	
	__tablename__ = 'discussion'
	
	id = Column(Integer, primary_key=True)
	title = Column(String(80), nullable=False)
	content = Column(String, nullable=False)
	creation_date = Column(Date, nullable=False)
	article_id = Column(Integer, ForeignKey('article.id'))
	article = relationship(Chapter)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	user_name = Column(String)
	user_picture = Column(String)
	
	
class DiscussionMessage(Base):
	
	__tablename__ = 'discussionmessage'
	
	id = Column(Integer, primary_key=True)
	content = Column(String, nullable=False)
	date = Column(Date, nullable=False)
	discussion_id = Column(Integer, ForeignKey('discussion.id'))
	discussion = relationship(Discussion)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)


class ChapterHistoric(Base):
	
	__tablename__ = 'articlehistoric'
	
	id = Column(Integer, primary_key=True)
	description = Column(String, nullable=False)
	date = Column(Date, nullable=False)
	article_id = Column(Integer, ForeignKey('article.id'))
	article = relationship(Chapter)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	user_name = Column(String)
	user_picture = Column(String)
	
	
class ChapterExercice(Base):
	
	__tablename__ = 'articleexercice'
	
	id = Column(Integer, primary_key=True)
	title = Column(String, nullable=False)
	content = Column(String, nullable=False)
	answer = Column(String, nullable=False)
	article_id = Column(Integer, ForeignKey('article.id'))
	article = relationship(Chapter)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	user_name = Column(String)
	user_picture = Column(String)
	is_verified = Column(Boolean)

engine = create_engine('sqlite:///main.db')

Base.metadata.create_all(engine)