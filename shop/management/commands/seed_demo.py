from django.core.management.base import BaseCommand

from shop.models import Discount, Item, Order, OrderItem, Tax


class Command(BaseCommand):
    help = "Seed demo data: items, order, discounts, taxes"

    def handle(self, *args, **options):
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Item.objects.all().delete()
        Discount.objects.all().delete()
        Tax.objects.all().delete()

        book = Item.objects.create(
            name="Book", description="Paper book", price=1999, currency="eur"
        )
        pen = Item.objects.create(
            name="Pen", description="Gel pen", price=499, currency="eur"
        )
        _ = Item.objects.create(
            name="Mug", description="Coffee mug", price=1299, currency="usd"
        )

        disc = Discount.objects.create(
            name="Spring -10%", percent_off=10.0, currency="eur"
        )
        vat = Tax.objects.create(name="VAT", percentage=20.0, inclusive=False)

        order = Order.objects.create(currency="eur")
        OrderItem.objects.create(order=order, item=book, quantity=2)
        OrderItem.objects.create(order=order, item=pen, quantity=3)
        order.discounts.add(disc)
        order.taxes.add(vat)

        self.stdout.write(self.style.SUCCESS("Seeded demo data."))
