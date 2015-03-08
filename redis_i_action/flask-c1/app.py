

import os
import sys
from flask import Flask,render_template,request,jsonify,session, \
				g, redirect, url_for,flash,get_flashed_messages
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect

from flask.ext.moment import Moment
from flask.ext.login import LoginManager,current_user, login_user,logout_user, login_required
from settings import Config
from collections import Counter
from werkzeug import secure_filename
from implement_func_redis import post_article,article_vote,\
					get_articles,add_remove_groups,get_group_articles
from flask.ext.restful import Api
from run_redis import conn
# import redis

import re
import requests
import time
from functools import wraps
# from rq import Queue,Connection
# from rq.job import Job
# from run_redis import conn

# pool = redis.ConnectionPool(host='localhost', port=6379, db=15)
# conn = redis.Redis(connection_pool=pool)
app = Flask(__name__,static_folder='static',
	template_folder='templates')


db = SQLAlchemy(app)
moment = Moment(app)
login = LoginManager(app)
# CsrfProtect(app)
api = Api(app)

from models import Article,User,Vote
from forms import LoginForm,SignUpForm,ArticleForm
from api_models import *
# security = Security(app, user_datastore)

# q = Queue(connection=conn)
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])



def allowed_file(filename):
	return '.' in filename and filename.lower().rsplit('.',1)[1] in ALLOWED_EXTENSIONS

#make a decorate for require login when visit a page
def login_required(callback):
	@wraps(callback)
	def decorated_function(*args, **kwargs):
		if g.user is None:
			return redirect(url_for('/login', next=request.url))
		return callback(*args, **kwargs)
	return decorated_function

@app.before_request
def before_request():
    g.user = current_user

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.after_request
def after_request(res):
    res.headers.add('Access-Control-Allow-Origin', '*')
    res.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    res.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return res

@app.route('/login',methods=['GET','POST'])
def login():
	if g.user is not None and current_user.is_authenticated():
		flash('You are already logged in','info')
		return redirect('/')
	form = LoginForm(request.form,csrf_enabled=True)
	if request.method == 'POST' and form.validate():
		email = form.email.data
		password = form.password.data
		user = User.query.filter_by(email=email).first()
		if user and user.check_password(password):
			login_user(user)
			flash('Login Success','success')
			return redirect(url_for('index'))
		else:
			flash('User not exists','warning')
			return render_template('login.html',form=form)

	if form.errors:
		flash(form.errors,'danger')
	return render_template('login.html',form=form)




@app.route('/',methods=['GET','POST'])
@login_required
def index():
	# results = {}
	# if request.method == "POST":
	# 	url = request.form['url']
	# 	if 'http://' not in url[:7]:
	# 		url = 'http://' + url
	# 		job = q.enqueue_call(
	# 			func=count_and_save_words, args=(url,), result_ttl=5000
	# 			)
	# 		print job.get_id()

	results = Article.query.all()[:10]

	return render_template('c1.html',results=results)

@app.route('/signup',methods=['POST','GET'])
def signup():
	if session.get('email'):
		flash('You are already loggin','info')
		return redirect(url_for('index'))
	form = SignUpForm(request.form,csrf_enabled=True)
	if request.method == 'POST' and form.validate():
		name = request.form.get('name')
		password = request.form.get('password')
		email = request.form.get('email')
		active = True
		exists_user = User.query.filter_by(email=email).first()
		if exists_user:
			flash('Email is exists, please use another email or login','warning')
			return render_template('signup.html',form = form)
		user = User(name,password,email,active)
		db.session.add(user)
		db.session.commit()
		flash('You are register success','success')
		return redirect(url_for('login'))
	if form.errors:
		flash(form.errors,'warning')
	return render_template('signup.html',form=form)


@app.route('/create-article',methods=['POST','GET'])
@login_required
def create_article():
	form = ArticleForm(request.form,csrf_enabled=True)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		link = form.link.data
		image = request.files['image']
		filename = ''
		if image and allowed_file(image.filename):
			filename = secure_filename(image.filename)
			image.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
		# now = time.time()
		# poster = current_user.id
		# scores = now + 432
		# votes = 1
		post_article(conn,current_user.name,title,link,os.path.join(app.config['UPLOAD_FOLDER'],filename))
		# article = Article(title,link,poster,now,scores,votes,filename)
		# db.session.add(article)
		# db.session.commit()
		flash('You are create new article success','success')
		return redirect(url_for('index'))
	if form.errors:
		flash(form.errors,'warning')
	return render_template('create_article.html',form=form)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('login'))



api.add_resource(ArticleResource,
	'/get_list_data',
	'/get_list_data/<string:id>'
)
api.add_resource(ArticleUpdateResource,
	'/put_data/<string:id>'
)

if __name__ == '__main__':
	app.config.from_object(Config.APP_SETTINGS)
	app.run()
