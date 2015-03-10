from django.conf.urls import patterns, include, url
from .views import HelloView
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'django_c2.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'',HelloView.as_view(),name="index"),
)
