from my_app import db
import datetime
from wtforms import FileField

# class Product(db.Document):
# 	created_at = db.DateTimeField(
# 		default=datetime.datetime.now, required=True
# 		)
# 	key = db.StringField(max_length=255, required=True)
# 	name = db.StringField(max_length=255, required=True)
# 	price = db.DecimalField()
# 	def __repr__(self):
# 		return '<Product %r>' % self.id

class Product(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	price = db.Column(db.Float)
	category_id = db.Column(db.Integer,
		db.ForeignKey('category.id'))
	category = db.relationship(
		'Category', backref=db.backref('products', lazy='dynamic')
		)
	image_path = db.Column(db.String(255))

	company = db.Column(db.String(100))

	def __init__(self, name, price, category,company,image_path):
		self.name = name
		self.price = price
		self.category = category
		self.company = company
		self.image_path = image_path

	def __repr__(self):
		return '<Product %d>' % self.id

class Category(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return '<Category %d>' % self.id
