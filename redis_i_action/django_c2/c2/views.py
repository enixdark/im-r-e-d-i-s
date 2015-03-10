from django.shortcuts import render,render_to_response
from django.views.generic import View
# Create your views here.

class HelloView(View):

	template_name = 'index.html'
	def get(self,request,*args,**kwargs):
		return render(request,self.template_name)
