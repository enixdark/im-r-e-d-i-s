from werkzeug import abort
from flask import render_template,Blueprint

from my_app.product.models import PRODUCTS
from datetime import datetime
product_blueprint = Blueprint('product',__name__)

@product_blueprint.route('/')
@product_blueprint.route('/home')
def home():
	return render_template('product/index.html',products=PRODUCTS)

@product_blueprint.route('/product/<key>')
def product(key):
	# import ipdb; ipdb.set_trace()
	product = PRODUCTS.get(key)
	if not product:
		abort(404)
	return render_template('product/product.html',product=product,timestamp = datetime.now().replace(minute = 0))

@product_blueprint.context_processor
def some_processor():
	def full_name(product):
		return '{0} / {1}'.format(product['category'],product['name'])
	return {'full_name':full_name}

# @product_blueprint.template_filter('full_name')
# def full_name(product):
# 	return '{0} / {1}'.format(product['category'],product['name'])
