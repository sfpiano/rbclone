from django.conf import settings
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # TODO - This is deprecated
    url(r'^$', 'django.views.generic.simple.redirect_to', {'url': 'r/'}),

    #url(r'^dashboard/$',
    #  'reviewboard.reviews.views.dashboard', name="dashboard"),
    url(r'^r/', include('reviews.urls')),

    url(r'^polls/', include('polls.urls')),
    url(r'^diff/', include('diffviewer.urls')),
    url(r'^account/', include('accounts.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('django.contrib',
    url(r'^account/logout/$', 'auth.views.logout',
        {'next_page': settings.LOGIN_URL}, name="logout")
)

from djangorestframework.resources import ModelResource
from djangorestframework.views import View, ListModelView, ListOrCreateModelView, InstanceModelView
from djangorestframework.response import Response
from djangorestframework.renderers import DEFAULT_RENDERERS
from djangorestframework import status
from diffviewer.models import FileDiff, ReviewFile

class MyResource(ModelResource):
  model = ReviewFile

class MyRoot(ListOrCreateModelView):
  renderers = DEFAULT_RENDERERS

  def post(self, request):
    try:
      obj = self.resource.model.objects.filter(
              filename=request.POST.__getitem__('filename'),
              revision=request.POST.__getitem__('revision'))
      if obj.count() != 0:
        return Response(status.HTTP_406_NOT_ACCEPTABLE,
                        headers={'Reason': 'Duplicate entry'})
    except:
      pass
    return ListOrCreateModelView.post(self, request)
    #return Response(status.HTTP_404_NOT_FOUND, headers={'Location': 'Asdf'})

urlpatterns += patterns('',
  #url(r'^api/$', ListOrCreateModelView.as_view(resource=MyResource)),
  url(r'^api/$', MyRoot.as_view(resource=MyResource), name='MyRoot'),
  url(r'^api/(?P<pk>[0-9]+)/$', InstanceModelView.as_view(resource=MyResource)),
)
