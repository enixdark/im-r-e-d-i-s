from my_app import db
from werkzeug.security import generate_password_hash,check_password_hash

class User(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(100))
	email = db.Column(db.String(255),unique=True)
	password = db.Column(db.String())

	def __init__(self,username,password,email):
		self.username = username
		self.setpassword(password)
		self.email = email

	def setpassword(self,password):
		self.password = generate_password_hash(password)

	def check_password(self,password):
		return check_password_hash(self.password,password)

	def is_authenticated(self):
		return True
	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id)


	def __repr__(self):
		return '<User %s>' % self.email


