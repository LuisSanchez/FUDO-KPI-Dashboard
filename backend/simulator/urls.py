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
    path("data/product-prices/", views.product_prices_data, name="product_prices_data"),
    path(
        "simulate/price-cost/", views.price_cost_simulator, name="price_cost_simulator"
    ),
    path("reset/", views.reset_data, name="reset_data"),
    path("report/pdf/", views.download_report, name="download_report"),
]
