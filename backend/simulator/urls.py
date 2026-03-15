from django.urls import path
from . import views

urlpatterns = [
    path('upload-sales/', views.upload_sales, name='upload_sales'),
    path('upload-expenses/', views.upload_expenses, name='upload_expenses'),
    path('products/', views.get_products, name='get_products'),
    path('calculate/', views.calculate, name='calculate'),
    path('reset/', views.reset_data, name='reset_data'),
]