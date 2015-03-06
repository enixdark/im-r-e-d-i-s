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
from redis import Redis

redis = Redis()

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
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
# app.config['MONGODB_SETTING'] = {'DB':'my_catalog'}
app.debug = True

# db = MongoEngine(app)
migrate = Migrate(app,db)

from my_app.catalog.views import catalog
from my_app.auth.views import auth
app.register_blueprint(auth)
app.register_blueprint(catalog)

manager = Manager(app)
manager.add_command('db',MigrateCommand)

# db.create_all()

