import os
from flask import request,jsonify,Blueprint,\
					render_template,redirect,flash,url_for,session

from my_app import app, db, api
from my_app.catalog.models import Product,Category
from sqlalchemy.orm.util import join
from my_app import redis,ALLOWED_EXTENSIONS
from forms import ProductForm, CategoryForm
from werkzeug import secure_filename
from flask.ext.restful import Resource
from flask.ext.restful import reqparse
from flask import jsonify
import json
catalog = Blueprint('catalog',__name__)

# api.create_api(Product,methods=['POST','GET','DELETE','PUT'])
# api.create_api(Category,methods=['POST','GET','DELETE','PUT'])
parser = reqparse.RequestParser()
parser.add_argument('name', type=str)
parser.add_argument('price', type=float)
parser.add_argument('category', type=dict)

class ProductApi(Resource):
	def post(self):
		args = parser.parse_args()
		name = args['name']
		price = args['price']
		categ_name = args['category']['name']
		category = Category.query.filter_by(name=categ_name).first()
		if not category:
			category = Category(categ_name)
			product = Product(name, price, category)
			db.session.add(product)
			db.session.commit()
			res = {}
			res[product.id] = {
			'name': product.name,
			'price': product.price,
			'category': product.category.name,
			}
		return json.dumps(res)

	def put(self,id):
		args = parser.parse_args()
		name = args['name']
		price = args['price']
		categ_name = args['category']['name']
		category = Category.query.filter_by(name=categ_name).first()
		Product.query.filter_by(id=id).update({
			'name': name,
			'price': price,
			'category_id': category.id,
			})
		db.session.commit()
		product = Product.query.get_or_404(id)
		res = {}
		res[product.id] = {
		'name': product.name,
		'price': product.price,
		'category': product.category.name,
		}
		return json.dumps(res)

	def get(self,id=None,page=1):
		if not id:
			products = Product.query.paginate(page, 10).items
		else:
			products = [Product.query.get(id)]
		if not products:
			abort(404)
		res = {}
		for product in products:
			res[product.id] = {
			'name': product.name,
			'price': product.price,
			'category': product.category.name
			}
		return json.dumps(res)

	def delete(Self,id):
		product = Product.query.filter_by(id=id)
		product.delete()
		db.session.commit()
		return json.dumps({'response': 'Success'})


api.add_resource(ProductApi,
	'/api/product',
	'/api/product/<int:id>',

	)
