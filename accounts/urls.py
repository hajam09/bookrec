from django.urls import path
from django.urls import include
from accounts import views

app_name = "accounts"

urlpatterns = [
	path('login/', views.login, name='login'),
	path('register/', views.register, name='register'),
	path('logout/', views.logout, name='logout'),
	# path('profile/', views.profile, name='profile'),
	# path('activate/<uidb64>/<token>', views.activateaccount, name='activate'),
	# path('password_request/', views.password_request, name='password_request'),
	# path('password_change/<uidb64>/<token>', views.password_change, name='password_change'),
]