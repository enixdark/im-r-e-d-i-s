import os,sys

_basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	DEBUG = False
	TESTING = False
	SECRET_KEY = 'please fill your secret key'
	CSRF_ENABLED = True
	APP_SETTINGS="settings.DevelopmentConfig"
	# DATABASE_URI = os.environ['DATABASE_URL']
	DATABASE_URI = "postgresql://localhost/redis"

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
