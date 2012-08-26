from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    #url(r'^login/$', 'accounts.views.login'),
    url(r'^login/$', 'django.contrib.auth.views.login', name="login"),
)
