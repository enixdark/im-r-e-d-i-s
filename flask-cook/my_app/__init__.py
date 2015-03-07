import os
from flask import Flask,render_template
from moment import momentjs
from flask_wtf.csrf import CsrfProtect
# from my_app.product.views import product_blueprint
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.openid import OpenID
# from flask.ext.mongoengine import MongoEngine
from flask.ext.migrate import Migrate,MigrateCommand
from flask.ext.script import Manager
from flask_oauth import OAuth
# from flask.ext.restless import APIManager
from redis import Redis
from flask.ext.restful import Api
redis = Redis()
oauth = OAuth()



twitter = oauth.remote_app('twitter',
	base_url = 'https://api.twitter.com/1.1/',
	request_token_url='https://api.twitter.com/oauth/request_token',
	access_token_url='https://api.twitter.com/oauth/access_token',
	authorize_url='https://api.twitter.com/oauth/authenticate',
	consumer_key='TdE45L4mH7XSTXZ1ZWup92RY6',
	consumer_secret='8lPcGXbefN3QO2IpdVVVKnpxsjYxGkUM8VDh9zKsbyuxpe0d2m'
)

#set file extension for upload
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__,template_folder='templates',static_folder='static',
	instance_path=os.path.join( os.path.dirname(os.path.dirname(__file__)),'my_app/instance'),instance_relative_config=True)
app.jinja_env.globals['momentjs'] = momentjs
app.config.from_pyfile('development.cfg',silent=False)
CsrfProtect(app)
@app.errorhandler(404)
def page_404(e):
	return render_template('error/404.html'), 404

@app.errorhandler(500)
def page_500(e):
	return render_template('error/500.html'), 500
# app.register_blueprint(product_blueprint)
db = SQLAlchemy(app)
oid = OpenID(app, 'openid-store')
#set login
# api = APIManager(app, flask_sqlalchemy_db=db)
api = Api(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
app.debug = True

migrate = Migrate(app,db)

from my_app.catalog.views import catalog
# from my_app.auth.views import auth
# app.register_blueprint(auth)
app.register_blueprint(catalog)

manager = Manager(app)
manager.add_command('db',MigrateCommand)


