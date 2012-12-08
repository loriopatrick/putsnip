from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^preview$', 'putsnip.preview.main'),
    url(r'^add[/]?$', 'putsnip.entry.add'),
    url(r'^s/(?P<key>.+)[/]?$', 'putsnip.entry.snippet'),
    url(r'^(?P<type>.+)/(?P<key>.+)[/]?$', 'putsnip.entry.redirect'),
    url(r'^[/]?$', 'putsnip.entry.filter'),
    url(r'^login[/]?$', 'putsnip.entry.login'),
    # Examples:
    # url(r'^$', 'putsnip.views.home', name='home'),
    # url(r'^putsnip/', include('putsnip.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
