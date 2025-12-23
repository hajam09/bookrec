from django.urls import path, include
from rest_framework import routers

from core import views
from core.api import (
    RequestAccountDeleteCodeApiVersion1,
    UserDataJsonApiVersion1,
    BookReviewActionApiVersion1,
    BookReviewVotingApiVersion1,
    UserActivityApiVersion1,
    UserShelfApiVersion1,
    UserReadingInfoApiVersion1,
)
from core.views import (
    loginView,
    logoutView,
    registerView,
    activateAccountView,
    forgotPasswordView,
    setPasswordView
)

app_name = 'core'
router = routers.DefaultRouter()

accountUrls = [
    path('login/', loginView, name='login-view'),
    path('logout/', logoutView, name='logout-view'),
    path('register/', registerView, name='register-view'),
    path('activate-account/<base64>/<token>/', activateAccountView, name='activate-account'),
    path('forgot-password/', forgotPasswordView, name='forgot-password-view'),
    path('set-password/<base64>/<token>', setPasswordView, name='set-password-view'),
]

coreUrls = [
    path('', views.indexView, name='index-view'),
    path('book-list', views.bookListView, name='book-list-view'),
    path('book/<int:isbn13>/', views.bookDetailView, name='book-detail-view'),
    path('user-shelf/', views.userShelfView, name='user-shelf-view'),
    path('settings/', views.SettingsView.as_view(), name='settings-view'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', include(router.urls)),
]

accountApiUrls = [
    path(
        'api/v1/requestAccountDeleteCodeApiVersion1',
        RequestAccountDeleteCodeApiVersion1.as_view(),
        name='requestAccountDeleteCodeApiVersion1'
    ),
    path(
        'api/v1/userDataJsonApiVersion1',
        UserDataJsonApiVersion1.as_view(),
        name='userDataJsonApiVersion1'
    )
]

coreApiUrls = [
    path(
        'api/v1/bookReviewActionApiVersion1/<slug:isbn13>/',
        BookReviewActionApiVersion1.as_view(),
        name='bookReviewActionApiVersion1'
    ),
    path(
        'api/v1/bookReviewVotingApiVersion1',
        BookReviewVotingApiVersion1.as_view(),
        name='bookReviewVotingApiVersion1'
    ),
    path(
        'api/v1/userActivityApiVersion1',
        UserActivityApiVersion1.as_view(),
        name='userActivityApiVersion1'
    ),
    path(
        'api/v1/userShelfApiVersion1',
        UserShelfApiVersion1.as_view(),
        name='userShelfApiVersion1'
    ),
    path(
        'api/v1/userReadingInfoApiVersion1/<slug:isbn13>/',
        UserReadingInfoApiVersion1.as_view(),
        name='userReadingInfoApiVersion1'
    )
]

urlpatterns = accountUrls + coreUrls + accountApiUrls + coreApiUrls
