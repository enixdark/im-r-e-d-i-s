from app import db
from sqlalchemy.dialects.postgresql import JSON
# from flask.ext.security import Security, SQLAlchemyUserDatastore,\
# 							UserMixin, RoleMixin, login_required

from werkzeug.security import generate_password_hash,check_password_hash


class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(255))
	email = db.Column(db.String(255),unique=True)
	password = db.Column(db.String(255))
	active = db.Column(db.Boolean())
	confirmed_at = db.Column(db.DateTime())
	def __init__(self,name,email,password,active,confirmed_at):
		self.name = name
		self.email = email
		self.set_password(password)
		self.active = active
		self.confirmed_at = confirmed_at

	def set_password(self, password):
		self.password = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password, password)

	def __repr__(self):
		return '<id {}'.format(self.id)

class Article(db.Model):
	__tablename__ = 'articles'
	id = db.Column(db.Integer,primary_key=True)
	title = db.Column(db.String())
	link = db.Column(db.String())
	poster = db.Column(db.Integer,db.ForeignKey('users.id'))
	time = db.Column(db.Float)
	scores = db.Column(db.Float)
	votes = db.Column(db.Integer)

	def __init__(self,title,link,poster,time,scores,votes):
		self.title = title
		self.link = link
		self.poster = poster
		self.time = time
		self.scores = scores
		self.votes = votes

	def __repr__(self):
		return '<id {}'.format(self.id)

class Vote(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	article = db.Column(db.Integer,db.ForeignKey('articles.id'))
	user = db.Column(db.Integer,db.ForeignKey('users.id'))
	likes = db.Column(db.Boolean)
	def __init__(self,article,user,likes):
		self.article = article
		self.user = user
		self.likes = likes
	def __repr__(self):
		return '<user-{}'.format(self.user)

# user_datastore = SQLAlchemyUserDatastore(db, User)
