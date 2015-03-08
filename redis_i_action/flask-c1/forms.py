from wtforms import TextField,BooleanField,PasswordField,IntegerField,FloatField,FileField
from flask_wtf import Form
from flask.ext.wtf.html5 import URLField
from wtforms.validators import ValidationError,InputRequired,EqualTo
from models import User
import re

EMAIL_VALIDATE = "^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"

def check_duplicate(case_sentisive=True):
	def _check_duplicate(form,field):
		if case_sentisive:
			res = User.query.filter(
				User.email.like('%' + field.data + '%')
			).first()
		else:
			res = User.query.filter(
				User.email.ilike('%' + field.data + '%')
			).first()
		if res:
			raise ValidationError('Email %s already exists' % field.data)
	return _check_duplicate

class EmailField(TextField):
	def pre_validate(self,form):
		match = re.compile(EMAIL_VALIDATE).match(form.email.data)
		if not match:
			raise ValidationError('The email is not extract')
		return super(EmailField,self).pre_validate(form)


class SignUpForm(Form):
	name = TextField('Name',validators=[InputRequired()])
	email = EmailField('Email',validators=[
		InputRequired(),check_duplicate()
		])

	password = PasswordField('Password',validators=[
			InputRequired(),EqualTo('password_confirmation', message = 'Passwords must match')
		])
	password_confirmation = PasswordField('Confirmation Password',validators=[InputRequired()])


class LoginForm(Form):
	email = TextField("Email",[InputRequired()])
	password = PasswordField('Password',[InputRequired()])

class ArticleForm(Form):
	title = TextField("Title",[InputRequired()])
	link = URLField('Link')
	image = FileField('Image image')
	# poster = IntegerField("Poster")
	# time = FloatField('Time')
	# scores = FloatField('Scores')
	# votes = db.Column(db.Integer)

