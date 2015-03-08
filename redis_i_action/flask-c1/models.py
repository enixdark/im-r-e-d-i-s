from app import db
from sqlalchemy.dialects.postgresql import JSON
# from flask.ext.security import Security, SQLAlchemyUserDatastore,\
# 							UserMixin, RoleMixin, login_required

from werkzeug.security import generate_password_hash,check_password_hash
from datetime import date,datetime

class Serialize(object):
    __public__ = None

    def tran_serialize(self, exclude=(), extra=()):
        data = {}
        keys = self._sa_instance_state.attrs.items()
        # import ipdb; ipdb.set_trace()
        public = self.__public__ + extra if self.__public__ else extra
        for k, field in  keys:
            if public and k not in public: continue
            if k in exclude: continue
            value = self._serialize(field.value)
            if value or value==0:
                data[k] = value
        return data

    @classmethod
    def _serialize(cls, value, follow_fk=False):
        if type(value) in (datetime, date):
            ret = value.isoformat()
        elif hasattr(value, '__iter__'):
            ret = []
            for v in value:
                ret.append(cls._serialize(v))
        elif Serialize in value.__class__.__bases__:
            ret = value.get_public()
        else:
            ret = value

        return ret

class User(db.Model,Serialize):
	__tablename__ = 'users'
	__public__ = ('id','name','email','password','active','confirmed_at')
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(255))
	email = db.Column(db.String(255),unique=True)
	password = db.Column(db.String(255))
	active = db.Column(db.Boolean())
	confirmed_at = db.Column(db.DateTime())
	def __init__(self,name,password,email,active,confirmed_at=datetime.now()):
		self.name = name
		self.email = email
		self.set_password(password)
		self.active = active
		self.confirmed_at = confirmed_at

	def set_password(self, password):
		self.password = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password, password)

	def __repr__(self):
		return '<id {}'.format(self.id)

	def isadmin(self):
		return self.admin

	def is_authenticated(self):
		return True
	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id)

class Article(db.Model,Serialize):
	__tablename__ = 'articles'
	__public__ = ('id','title','link','poster','time','scores','votes')
	id = db.Column(db.Integer,primary_key=True)
	title = db.Column(db.String())
	link = db.Column(db.String())
	poster = db.Column(db.Integer,db.ForeignKey('users.id'))
	time = db.Column(db.Float)
	scores = db.Column(db.Float)
	votes = db.Column(db.Integer)
	image = db.Column(db.String(255))

	def __init__(self,title,link,poster,time,scores,votes,image):
		self.title = title
		self.link = link
		self.poster = poster
		self.time = time
		self.scores = scores
		self.votes = votes
		self.image = image
	def __repr__(self):
		return '<id {}'.format(self.id)

class Vote(db.Model,Serialize):
	__public__ = ('id','article','user','likes')
	id = db.Column(db.Integer,primary_key=True)
	article = db.Column(db.Integer,db.ForeignKey('articles.id'))
	user = db.Column(db.Integer,db.ForeignKey('users.id'))
	likes = db.Column(db.Boolean)
	def __init__(self,article,user,likes):
		self.article = article
		self.user = user
		self.likes = likes
	def __repr__(self):
		return '<user-{}'.format(self.user)

# user_datastore = SQLAlchemyUserDatastore(db, User)
