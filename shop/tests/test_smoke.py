from django.urls import reverse

from shop.models import Item


def test_item_page(client, db):
    item = Item.objects.create(name="T", description="D", price=100, currency="eur")
    url = reverse("item_detail", args=[item.id])
    resp = client.get(url)
    assert resp.status_code == 200
