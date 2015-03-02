

import os
import sys
from flask import Flask,render_template,request,jsonify,\
				g, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext.moment import Moment
from settings import Config
from collections import Counter

import re
import requests
import time
from functools import wraps

# from rq import Queue,Connection
# from rq.job import Job
# from run_redis import conn

app = Flask(__name__,static_folder='static',
	template_folder='templates')

db = SQLAlchemy(app)
moment = Moment(app)

from models import Article,User,Vote

# security = Security(app, user_datastore)

# q = Queue(connection=conn)



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
    g.user = None

@app.route('/login',methods=['GET','POST'])
def login():
	return render_template('login.html')


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


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)


if __name__ == '__main__':
	app.config.from_object(Config.APP_SETTINGS)
	app.run()
