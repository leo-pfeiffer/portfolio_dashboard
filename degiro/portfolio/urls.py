from django.urls import path
from . import views

app_name = 'portfolio'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('portfolio-allocation/', views.portfolio_allocation, name='portfolio-allocation'),
    path('portfolio-overview/', views.portfolio_allocation2, name='portfolio-overview'),
]