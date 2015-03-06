from my_app.auth.models import User
from flask import request,redirect,render_template,flash,\
		Blueprint,url_for,session
from my_app import app,db
from forms import LoginForm,RegistrationForm


auth = Blueprint('auth',__name__)


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
def login():
	form = LoginForm(request.form,csrf_enabled=True)
	if request.method == 'POST' and form.validate():
		email = request.form.get('email')
		password = request.form.get('password')
		get_user = User.query.filter_by(email=email).first()
		if email and get_user.check_password(password):
			session['email'] = email
			flash('You have successfully logged in.', 'success')
			return redirect('/')
	if form.errors:
		flash(form.errors,'warning')
	return render_template('auth/login.html',form=form)

@auth.route('/logout')
def logout():
	if session.get('email'):
		del session['email']
		flash('You have successfully logged out.', 'success')
	return redirect('/')
