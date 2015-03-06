import os
from flask import request,jsonify,Blueprint,\
					render_template,redirect,flash,url_for,session

from my_app import app, db
from my_app.catalog.models import Product,Category
from sqlalchemy.orm.util import join
from my_app import redis,ALLOWED_EXTENSIONS
from forms import ProductForm, CategoryForm
from werkzeug import secure_filename

catalog = Blueprint('catalog',__name__)

from functools import wraps


def allowed_file(filename):
	return '.' in filename and filename.lower().rsplit('.',1)[1] in ALLOWED_EXTENSIONS

def template_ot_json(template=None):
	def decorated(f):
		@wraps(f)
		def decorated_fn(*args,**kwargs):
			ctx = f(*args,**kwargs)
			if request.is_xhr or not template:
				return jsonify(ctx)
			else:
				return render_template(template,**ctx)
		return decorated_fn
	return decorated

@catalog.route('/')
@catalog.route('/home')
@template_ot_json('catalog/index.html')
def home():
	# if request.is_xhr:
	products = Product.query.all()
	return { 'count': len(products) }
	# return render_template('catalog/index.html')


"""Use for mongodb """
# @catalog.route('/product/<key>')
# def product(key):
# 	product = Product.objects.get_or_404(key=key)
# 	product_key = 'product-%s' % product.key
# 	redis.set(product_key,product.name)
# 	redis.expire(product_key,600)
# 	return render_template('product/product.html',product=product)

# @catalog.route('/products')
# def products():
# 	products = Product.objects.all()
# 	res = {}
# 	for product in products:
# 		res[product.key] = {
# 			'name':product.name,
# 			'price':product.price
# 		}
# 	return jsonify(res)

# @catalog.route('/product-create',method=['POST'])
# def create_product():
# 	name = request.form.get('name')
# 	key = request.form.get('key')
# 	price = request.form.get('price')
# 	product = Product(
# 		name=name,
# 		key=key,
# 		price=Decimal(price)
# 		)
# 	product.save()
# 	return 'Product created.'

# @catalog.route('/category-create', methods=['POST',])
# def create_category():
# 	name = request.form.get('name')
# 	category = Category(name)
# 	db.session.add(category)
# 	db.session.commit()
# 	return 'Category created.'

""" uncomment if use SQL Database """
@catalog.route('/product/<id>')
def product(id):

	product = Product.query.get_or_404(id)
	product_key = 'product-%s' % product.id
	redis.set(product_key,product.name)
	redis.expire(product_key,600)
	return render_template('catalog/product.html',product=product)

@catalog.route('/products')
@catalog.route('/products/<int:page>')
def products(page=1):
	products = Product.query.paginate(page,10)
	# res = {}
	# for product in products:
	# 	res[product.id] = {
	# 		'name':product.name,
	# 		'price':str(product.price),
	# 		'category': product.category.name
	# 	}
	# return jsonify(res)
	return render_template('catalog/products.html',products=products)

# @catalog.route('/product-create', methods=['POST','GET'])
# def create_product():
# 	if request.method == "POST":
# 		name = request.form.get('name')
# 		price = request.form.get('price')
# 		categ_name = request.form.get('category')
# 		category = Category.query.filter_by(name=categ_name).first()
# 		if not category:
# 			category = Category(categ_name)
# 		product = Product(name, price, category)
# 		db.session.add(product)
# 		db.session.commit()
# 		flash('The product %s has been created' % name, 'success')
# 		return redirect(url_for('catalog.product', id=product.id))
# 	else:
# 		categories = Category.query.all()
# 	return render_template('catalog/product-create.html',categories=categories)

@catalog.route('/product-create', methods=['POST','GET'])
def create_product():
	form = ProductForm(request.form,csrf_enabled=True)
	category = [(c.id,c.name) for c in Category.query.all()]
	form.category.choices = category
	form.company.choices = [(1,1)]
	# import ipdb; ipdb.set_trace()
	if request.method == 'POST' and form.validate():
		name = request.form.get('name')
		price = request.form.get('price')

		category = Category.query.get_or_404(
			request.form.get('category')
		)
		image = request.files['image_path']
		filename = ''
		if image and allowed_file(image.filename):
			filename = secure_filename(image.filename)
			image.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
		company = 1

		product = Product(name,price,category,company,filename)
		db.session.add(product)
		db.session.commit()
		flash('The product %s has been created ' % name,'success')
		return redirect(url_for('catalog.product',id=product.id))
	print form.errors
	if form.errors:
		flash(form.errors, 'danger')
	return render_template('catalog/product-create.html',form = form)

@catalog.route('/category-create', methods=['POST','GET'])
def create_category():
	# name = request.form.get('name')
	form = CategoryForm(request.form,csrf_enabled=True)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		category = Category(name)
		db.session.add(category)
		db.session.commit()
		flash('The category %s has been created' % name,'success')
		return redirect(url_for('catalog.category',id=category.id))
	if form.errors:
		flash(form.errors,'danger')
	return render_template('catalog/category-create.html',form=form)

@catalog.route('/category/<id>')
def category(id):
	category = Category.query.get_or_404(id)
	return render_template('catalog/category.html',category=category)

@catalog.route('/categories')
def categories():
	categories = Category.query.all()
	res = {}
	for category in categories:
		res[category.id] = {
		'name': category.name
		}
		for product in category.products:
			res[category.id]['products'] = {
				'id': product.id,
				'name': product.name,
				'price': product.price
			}
	return render_template('catalog/categories.html',categories=categories)

@catalog.route('/recent-products')
def recent_products():
	key_alive = redis.keys('product-*')
	products = [redis.get(k) for k in keys_alive]
	return jsonify({'products':products})
@catalog.context_processor
def some_processor():
	def full_name(product):
		return '{0} / {1}'.format(product.category.name,product.name)
	return {'full_name':full_name}

@catalog.route('/product-search')
@catalog.route('/product-search/<int:page>')
def product_search(page=1):
	name = request.args.get('name')
	price = request.args.get('price')
	company = request.args.get('company')
	category = request.args.get('category')
	products = Product.query
	if name:
		products = products.filter(Product.name.like('%' + name +
			'%'))
	if price:
		products = products.filter(Product.price == price)
	if company:
		products = products.filter(Product.company.like('%' +
		company + '%'))
	if category:
		products = products.select_from(join(Product,
			Category)).filter(
		Category.name.like('%' + category + '%')
		)
	return render_template('catalog/products.html', products=products.paginate(page, 10)
			)
