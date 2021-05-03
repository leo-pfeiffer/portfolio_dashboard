from django.urls import path
from . import views

app_name = 'portfolio'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('allocation/', views.Allocation.as_view(), name='allocation'),
    path('overview/', views.Overview.as_view(), name='overview'),
    path('performance/', views.Performance.as_view(), name='performance'),
    path('depot/', views.Depot.as_view(), name='depot'),
    path('create-report/', views.CreateReport.as_view(), name='create-report'),
    path('request-report/', views.RequestReport.as_view(), name='request-report'),
    path('contact/', views.ContactView.as_view(), name='portfolio-contact'),
]