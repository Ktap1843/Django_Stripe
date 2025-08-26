from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("item/<int:item_id>", views.item_detail, name="item_detail"),
    path("buy/<int:item_id>", views.buy_item, name="buy_item"),
    path("order/<int:order_id>", views.order_detail, name="order_detail"),
    path("buy-order/<int:order_id>", views.buy_order, name="buy_order"),
    path("success", views.success, name="success"),
    path("cancel", views.cancel, name="cancel"),
    path("webhooks/stripe", views.stripe_webhook, name="stripe_webhook"),
    path("orders/create", views.create_order, name="create_order"),
    path("orders/<int:order_id>/add", views.add_to_order, name="add_to_order"),
    path("orders/add", views.add_to_order_any, name="add_to_order_any"),
    path(
        "orders/<int:order_id>/set-currency",
        views.set_order_currency,
        name="set_order_currency",
    ),
]
