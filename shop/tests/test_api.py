import pytest
from django.urls import reverse

from shop.models import Item


@pytest.mark.django_db
def test_item_detail_and_buy(client):
    item = Item.objects.create(
        name="Demo", description="test", price=1000, currency="eur"
    )
    resp = client.get(reverse("item_detail", args=[item.id]))
    assert resp.status_code == 200
    assert b"Demo" in resp.content

    resp = client.get(reverse("buy_item", args=[item.id]))
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
