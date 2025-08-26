from django.core.validators import MinValueValidator
from django.db import models

CURRENCY_CHOICES = (
    ("eur", "EUR"),
    ("usd", "USD"),
)


class Item(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Unit amount in minor units (e.g. cents)",
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="eur")

    def __str__(self):
        return f"{self.name} ({self.currency.upper()} {self.price/100:.2f})"


class Discount(models.Model):
    name = models.CharField(max_length=120)
    percent_off = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    amount_off = models.PositiveIntegerField(
        null=True, blank=True, help_text="Minor units"
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="eur")

    def __str__(self):
        if self.percent_off is not None:
            kind = f"{self.percent_off}%"
        else:
            kind = f"{self.amount_off} {self.currency}"
        return f"{self.name} ({kind})"


class Tax(models.Model):
    name = models.CharField(max_length=120)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )
    inclusive = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class Order(models.Model):
    items = models.ManyToManyField("Item", through="OrderItem", related_name="orders")
    discounts = models.ManyToManyField(Discount, blank=True)
    taxes = models.ManyToManyField(Tax, blank=True)

    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="eur")
    paid = models.BooleanField(default=False)
    checkout_session_id = models.CharField(max_length=255, blank=True)
    payment_intent_id = models.CharField(max_length=255, blank=True)

    def total_amount_minor(self) -> int:
        return sum(
            oi.quantity * oi.item.price
            for oi in self.orderitem_set.select_related("item")
        )

    def __str__(self):
        return f"Order #{self.pk} — {self.currency.upper()} {self.total_amount_minor()/100:.2f}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ("order", "item")
