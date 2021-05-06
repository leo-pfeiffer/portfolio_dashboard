from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'portfolio'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('contact/', views.ContactView.as_view(), name='portfolio-contact'),
]