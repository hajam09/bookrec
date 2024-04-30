from django.urls import path, include
from rest_framework import routers

from core import views
from core.api import *

app_name = 'core'
router = routers.DefaultRouter()

accountUrls = [
    path('login/', views.loginView, name='login-view'),
    path('logout/', views.logoutView, name='logout-view'),
    path('register/', views.registrationView, name='register-view'),
    path('account-activation-request/<base64>/<token>/', views.accountActivationRequest, name='account-activation-request'),
    path('password-change-request/', views.passwordChangeRequest, name='password-change-request'),
    path('password-update-request/<base64>/<token>/', views.passwordUpdateRequest, name='password-update-request'),
]

coreUrls = [
    path('', views.indexView, name='index-view'),
    path('book-list', views.bookListView, name='book-list-view'),
    path('book/<int:isbn13>/', views.bookDetailView, name='book-detail-view'),
    path('user-shelf/', views.userShelfView, name='user-shelf-view'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', include(router.urls)),
]

accountApiUrls = [
    path(
        'api/v1/requestDeleteCodeApiEventVersion1Component',
        RequestDeleteCodeApiEventVersion1Component.as_view(),
        name='requestDeleteCodeApiEventVersion1Component'
    )
]

coreApiUrls = [
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
    )
]

urlpatterns = accountUrls + coreUrls + accountApiUrls + coreApiUrls
