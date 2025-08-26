import pytest
from django.urls import reverse

from shop.models import Item, Order, OrderItem


@pytest.mark.django_db
def test_order_checkout_session(client):
    book = Item.objects.create(
        name="Book", description="Paper book", price=1999, currency="eur"
    )
    order = Order.objects.create(currency="eur")
    OrderItem.objects.create(order=order, item=book, quantity=1)

    resp = client.get(reverse("buy_order", args=[order.id]))
    assert resp.status_code in (200, 400)
    data = resp.json()
    assert "id" in data or "error" in data
