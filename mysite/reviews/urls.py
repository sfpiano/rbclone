from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'reviews.views.showreviews'),
    url(r'^bot/(?P<fileid>\d+)$', 'stylebot.analyzer.test'),
    url(r'^new/$', 'reviews.views.newreview'),
    url(r'^create/$', 'reviews.views.createReview', name='createReview'),
    url(r'^(?P<set_id>\d+)/comments/$', 'reviews.views.comments'),
    url(r'^(?P<set_id>\d+)/overview/$', 'reviews.views.overview'),
    url(r'^(?P<set_id>\d+)/diff/(?P<file_id>\d+)/$', 'reviews.views.diff'),
)

