from django.urls import path
from . import views

app_name = 'portfolio'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('portfolio-allocation/', views.portfolio_allocation, name='portfolio-allocation'),
    path('portfolio-overview/', views.portfolio_overview, name='portfolio-overview'),
    path('portfolio-performance/', views.portfolio_performance, name='portfolio-performance'),
    path('portfolio-depot/', views.portfolio_depot, name='portfolio-depot'),
]