from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'portfolio'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout', views.logout_view, name='logout'),
    path('allocation/', views.Allocation.as_view(), name='allocation'),
    path('overview/', views.Overview.as_view(), name='overview'),
    path('performance/', views.Performance.as_view(), name='performance'),
    path('depot/', views.Depot.as_view(), name='depot'),
    path('create-report/', views.CreateReport.as_view(), name='create-report'),
    path('request-report/', views.RequestReport.as_view(), name='request-report'),
    path('contact/', views.ContactView.as_view(), name='portfolio-contact'),
]