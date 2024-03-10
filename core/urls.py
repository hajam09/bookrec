from django.urls import path

from core import views
from core.api import *

app_name = 'core'

urlpatterns = [
    path('', views.indexView, name='index-view'),
    path('book-list', views.bookListView, name='book-list-view'),
    path('book/<int:isbn13>/', views.bookDetailView, name='book-detail-view'),
]

urlpatterns += [
    path(
        'api/v1/userReadingInfoApiEventVersion1Component/<slug:isbn13>',
        UserReadingInfoApiEventVersion1Component.as_view(),
        name='userReadingInfoApiEventVersion1Component'
    ),
    path(
        'api/v1/bookReviewActionApiEventVersion1Component/<slug:isbn13>',
        BookReviewActionApiEventVersion1Component.as_view(),
        name='bookReviewActionApiEventVersion1Component'
    ),
]
