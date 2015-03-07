from my_app.auth.models import User
from flask import request,redirect,render_template,flash,\
		Blueprint,url_for,session
from my_app import app,db,oid,login_manager,google
from forms import LoginForm,RegistrationForm,OpenIDForm

from flask import g
from flask.ext.login import current_user, login_user,logout_user, login_required
import requests

auth = Blueprint('auth',__name__)


GOOGLE_OAUTH2_USERINFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'

@login_manager.user_loader
def load_user(id):
	return User.query.get(int(id))

@auth.before_request
def get_current_user():
	g.user = current_user

@auth.route('/register',methods=['POST','GET'])
def register():
	if session.get('email'):
		flash('You are already loggin','info')
		return redirect('/')
	form = RegistrationForm(request.form,csrf_enabled=True)
	if request.method == 'POST' and form.validate():
		username = request.form.get('username')
		password = request.form.get('password')
		email = request.form.get('email')
		exists_user = User.query.filter_by(email=email).first()
		if exists_user:
			flash('Email is exists, please use another email or login','warning')
			return render_template('auth/register.html',form = form)
		user = User(username,password,email)
		db.session.add(user)
		db.session.commit()
		flash('You are register success','success')
		return redirect(url_for('auth.login'))
	if form.errors:
		flash(form.errors,'warning')
	return render_template('auth/register.html',form=form)

@auth.route('/login',methods=['POST','GET'])
@oid.loginhandler
def login():
	# form = LoginForm(request.form,csrf_enabled=True)
	# if request.method == 'POST' and form.validate():
	# 	email = request.form.get('email')
	# 	password = request.form.get('password')
	# 	get_user = User.query.filter_by(email=email).first()
	# 	if email and get_user.check_password(password):
	# 		session['email'] = email
	# 		flash('You have successfully logged in.', 'success')
	# 		return redirect('/')
	# if form.errors:
	# 	flash(form.errors,'warning')
	# return render_template('auth/login.html',form=form)
	if g.user is not None and current_user.is_authenticated():
		flash('You are already logged in','info')
		return redirect('/')
	form = LoginForm(request.form,csrf_enabled=True)
	openid_form = OpenIDForm(request.form)
	if request.method == 'POST':
		if request.form.has_key('openid'):
			openid_form.validate()
			if openid_form.errors:
				flash(openid.form.errors,'danger')
				return render_template('auth/login.html',form=form,openid_form=openid_form)
			openid = request.form.get('openid')
			return oid.try_login(openid,ask_for['email','nickname'])
		else:
			form.validate()
			if form.errors:
				flash(form.errors,'danger')
				return render_template('auth/login.html',form=form,openid_form=openid_form)
			email = request.form.get('email')
			password = request.form.get('password')
			exists_user = User.query.filter_by(email=email).first()
			if not (exists_user and exists_user.check_password(password)):
				flash('Invalid username or password. Please try again.','danger')
				return render_template('auth/login.html', form=form)
			login_user(exists_user)
			flash('You have successfully logged in.', 'success')
			return redirect('/')
	if form.errors:
		flash(form.errors,'warning')
	return render_template('auth/login.html',form=form,openid_form=openid_form)

# @auth.route('/logout')
# def logout():
# 	if session.get('email'):
# 		del session['email']
# 		flash('You have successfully logged out.', 'success')
# 	return redirect('/')

@auth.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect('/')

@auth.route('/google-login')
def google_login():
	return google.authorize(
		callback = url_for('auth.google_authorized',_external=True
			)
		)

@auth.route('/oauth2callback')
@google.authorized_handler
def google_authorized(res):
	if res is None:
		return 'Access denied: reason=%s' % (
			request.args['error_reason'],
			request.args['error_description']
			)
	session['google_oauth_token'] = (res['access_token'],'')
	userinfo = requests.get(GOOGLE_OAUTH2_USERINFO_URL,params=dict(
			access_token=res['access_token'],
		)).json()
	user = User.query.filter_by(email=userinfo['email']).first()
	if not user:
		user = User(userinfo['email'], '', userinfo['email'])
		db.session.add(user)
		db.session.commit()
	login_user(user)
	flash(
		'Logged in as id=%s ,name=%s' % (userinfo['id'],userinfo['name']),'success'
	)
	return redirect('/')

@google.tokengetter
def get_google_oauth_token():
	return session.get('google_oauth_token')
