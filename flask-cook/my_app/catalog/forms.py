from flask_wtf import Form
from wtforms import TextField,DecimalField,SelectField
from decimal import Decimal
from wtforms.validators import InputRequired,NumberRange,Optional
from models import Category,Product
from wtforms.validators import ValidationError
from wtforms.widgets import html_params,Select, HTMLString
from wtforms import FileField



def check_duplicate_category(case_sentisive=True):
	def _check_duplicate(form,field):
		if case_sentisive:
			res = Category.query.filter(
				Category.name.like('%' + field.data + '%')
			).first()
		else:
			res = Category.query.filter(
				Category.name.ilike('%' + field.data + '%')
			).first()
		if res:
			raise ValidationError('Category named %s already exists' % field.data)
	return _check_duplicate


class CustomCategoryInput(Select):
	def __call__(self,field,**kwargs):
		kwargs.setdefault('id',field.id)
		html = []
		for val, label, selected in field.iter_choices():
			html.append(
				'<input type="radio" %s> %s' % (html_params(name=field.name,value=val,checked=selected,**kwargs)
				,label)
			)
		return HTMLString(''.join(html))

class CategoryField(SelectField):
	"""docstring for CategoryField"""
	widget = CustomCategoryInput()
	def iter_choices(self):
		categories = [(c.id,c.name) for c in Category.query.all()]
		for value,label in categories:
			yield (value,label,self.coerce(value) == self.data)
	def pre_validate(self,form):
		# import ipdb; ipdb.set_trace()
		for (v,_) in [(c.id,c.name) for c in Category.query.all()]:
			if self.data == v:
				break
		else:
			raise ValueError(self.gettext('Not a valid choice'))
		return super(CategoryField,self).pre_validate(form)

class NameForm(Form):
	name = TextField('Name', validators=[InputRequired()])

class ProductForm(NameForm):
	price = DecimalField('Price',validators=[
		InputRequired(),NumberRange(min=Decimal('0.0'))
		])
	category = CategoryField('Category',validators=[InputRequired()],coerce=int)
	company = SelectField('Company',validators=[Optional()])
	# company = SelectField('Company')
	image_path = FileField('Product image')
class CategoryForm(NameForm):
	name = TextField('Name', validators=[
		InputRequired(),check_duplicate_category()
		])

