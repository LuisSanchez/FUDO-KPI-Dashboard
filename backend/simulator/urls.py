from django.urls import path
from . import views

urlpatterns = [
    path("upload-sales/", views.upload_sales, name="upload_sales"),
    path("upload-expenses/", views.upload_expenses, name="upload_expenses"),
    path("products/", views.get_products, name="get_products"),
    path("calculate/", views.calculate, name="calculate"),
    path("data/sales/", views.sales_table_data, name="sales_table_data"),
    path("data/expenses/", views.expenses_table_data, name="expenses_table_data"),
    path("data/charts/", views.chart_data, name="chart_data"),
    path("reset/", views.reset_data, name="reset_data"),
]
