from django.urls import path
from django.urls import re_path
from django.urls import include
from book import views
app_name = "book"

urlpatterns = [
	path('', views.mainpage, name='mainpage'),
	path('book-page/<slug:isbn_13>', views.bookPage, name='bookPage'),
	re_path(r'^book-page/book-comment/(?P<isbn_13>.*)/(?P<action>.*)$',views.bookComment, name='bookComment'),
	re_path(r'^updateShelf/(?P<isbn_13>.*)/(?P<shelf_type>.*)$',views.updateShelf, name='updateShelf'),
]