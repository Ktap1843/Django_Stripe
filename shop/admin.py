from django.contrib import admin

from .models import Discount, Item, Order, OrderItem, Tax


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "currency")
    list_filter = ("currency",)
    search_fields = ("name",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "currency", "paid")
    list_filter = ("currency", "paid")
    inlines = [OrderItemInline]
    filter_horizontal = ("discounts", "taxes")


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "percent_off", "amount_off", "currency")
    list_filter = ("currency",)


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "percentage", "inclusive")
