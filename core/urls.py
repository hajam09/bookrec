from django.urls import path, include
from rest_framework import routers

from core import views
from core.api import *

app_name = 'core'
router = routers.DefaultRouter()

urlpatterns = [
    path('', views.indexView, name='index-view'),
    path('book-list', views.bookListView, name='book-list-view'),
    path('book/<int:isbn13>/', views.bookDetailView, name='book-detail-view'),
    path('user-shelf/', views.userShelfView, name='user-shelf-view'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', include(router.urls)),
]

urlpatterns += [
    path(
        'api/v1/bookReviewActionApiEventVersion1Component/<slug:isbn13>/',
        BookReviewActionApiEventVersion1Component.as_view(),
        name='bookReviewActionApiEventVersion1Component'
    ),
    path(
        'api/v1/bookReviewVotingActionApiEventVersion1Component',
        BookReviewVotingActionApiEventVersion1Component.as_view(),
        name='bookReviewVotingActionApiEventVersion1Component'
    ),
    path(
        'api/v1/userShelfApiEventVersion1Component',
        UserShelfApiEventVersion1Component.as_view(),
        name='userShelfApiEventVersion1Component'
    ),
    path(
        'api/v1/userReadingInfoApiEventVersion1Component/<slug:isbn13>/',
        UserReadingInfoApiEventVersion1Component.as_view(),
        name='userReadingInfoApiEventVersion1Component'
    ),
]
