import os,sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

class Config(object):
	DEBUG = False
	TESTING = False
	SECRET_KEY = 'please fill your secret key'
	CSRF_ENABLED = True
	APP_SETTINGS="settings.DevelopmentConfig"
	# DATABASE_URI = os.environ['DATABASE_URL']
	DATABASE_URI = "postgresql://localhost/redis"
	SQLALCHEMY_DATABASE_URI = "postgresql://localhost:5432/redis"
	WTF_CSRF_ENABLED = True
	UPLOAD_FOLDER = BASE_DIR+'/flask-c1/static/media'

class ProductConfig(Config):
	DEBUG = False

class TestingConfig(Config):
	TESTING = True

class StagingConfig(Config):
	DEVELOPMENT = True
	DEBUG = True

class DevelopmentConfig(Config):
	DEVELOPMENT = True
	DEBUG = True
