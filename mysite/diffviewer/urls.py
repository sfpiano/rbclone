from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from diffviewer.models import FileDiff

urlpatterns = patterns('',
    url(r'^(?P<set_id>\d+)/gtg$', 'diffviewer.views.handleGTG'),
    #url(r'^(?P<set_id>\d+)/diff/(?P<file_id>\d+)$', 'diffviewer.views.diff', name="diffroot"),
    url(r'^(?P<set_id>\d+)/diff/(?P<file_id>\d+)/comment/$',
        'diffviewer.views.createComment', name="createComment"),
    url(r'^comment/(?P<comment_id>\d+)$',
        'diffviewer.views.deleteComment', name="deleteComment"),
    #url(r'^(?P<set_id>\d+)/comments/$', 'diffviewer.views.comments'),
    #url(r'^(?P<set_id>\d+)/overview/$', 'diffviewer.views.overview'),
)
