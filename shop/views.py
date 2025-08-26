import json
from decimal import ROUND_HALF_UP, Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Item, Order, OrderItem


def _get_keys_for_currency(currency: str) -> dict:
    keys = settings.STRIPE_KEYS_BY_CURRENCY.get(currency)
    if not keys or not keys.get("sk") or not keys.get("pk"):
        raise RuntimeError(f"Stripe keys not configured for currency: {currency}")
    return keys


def _convert_minor(amount_minor: int, from_cur: str, to_cur: str) -> int:
    from_cur = from_cur.lower()
    to_cur = to_cur.lower()
    if from_cur == to_cur:
        return int(amount_minor)

    rate = getattr(settings, "CURRENCY_RATES", {}).get((from_cur, to_cur))
    if not rate:
        raise RuntimeError(f"No FX rate configured for {from_cur}->{to_cur}")

    major = Decimal(amount_minor) / Decimal(100)
    converted_major = major * Decimal(str(rate))
    converted_minor = (converted_major * Decimal(100)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(converted_minor)


def index(request):
    items = Item.objects.all().order_by("id")
    orders = Order.objects.all().order_by("id")
    return render(request, "index.html", {"items": items, "orders": orders})


def item_detail(request, item_id: int):
    item = get_object_or_404(Item, pk=item_id)
    try:
        keys = _get_keys_for_currency(item.currency)
        stripe_pk = keys["pk"]
    except Exception:
        stripe_pk = ""
    return render(request, "item_detail.html", {"item": item, "stripe_pk": stripe_pk})


def order_detail(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)
    try:
        keys = _get_keys_for_currency(order.currency)
        stripe_pk = keys["pk"]
    except Exception:
        stripe_pk = ""
    return render(
        request, "order_detail.html", {"order": order, "stripe_pk": stripe_pk}
    )


def success(request):
    return render(
        request,
        "status.html",
        {"title": "Payment success", "text": "Thanks! Payment succeeded."},
    )


def cancel(request):
    return render(
        request,
        "status.html",
        {"title": "Payment canceled", "text": "Payment was canceled."},
    )


def buy_item(request, item_id: int):
    item = get_object_or_404(Item, pk=item_id)
    keys = _get_keys_for_currency(item.currency)
    stripe.api_key = keys["sk"]

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": item.currency,
                        "product_data": {
                            "name": item.name,
                            "description": item.description[:500],
                        },
                        "unit_amount": item.price,
                    },
                    "quantity": 1,
                }
            ],
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
        )
        return JsonResponse({"id": session.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def buy_order(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)
    keys = _get_keys_for_currency(order.currency)
    stripe.api_key = keys["sk"]

    tax_rate_ids = []
    for tax in order.taxes.all():
        tr = stripe.TaxRate.create(
            display_name=tax.name,
            percentage=float(tax.percentage),
            inclusive=tax.inclusive,
        )
        tax_rate_ids.append(tr.id)

    line_items = []
    for oi in order.orderitem_set.select_related("item"):
        unit_amount_conv = _convert_minor(
            oi.item.price, oi.item.currency, order.currency
        )
        item_data = {
            "price_data": {
                "currency": order.currency,
                "product_data": {"name": oi.item.name},
                "unit_amount": unit_amount_conv,
            },
            "quantity": oi.quantity,
        }
        if tax_rate_ids:
            item_data["tax_rates"] = tax_rate_ids
        line_items.append(item_data)

    discounts = []
    for disc in order.discounts.all():
        if disc.percent_off is not None:
            coupon = stripe.Coupon.create(
                name=disc.name, percent_off=float(disc.percent_off), duration="once"
            )
        else:
            amount_off = int(disc.amount_off or 0)
            if amount_off <= 0:
                continue
            amount_off_conv = _convert_minor(amount_off, disc.currency, order.currency)
            coupon = stripe.Coupon.create(
                name=disc.name,
                amount_off=amount_off_conv,
                currency=order.currency,
                duration="once",
            )
        discounts.append({"coupon": coupon.id})

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=line_items,
            discounts=discounts if discounts else None,
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
        )
        order.checkout_session_id = session.id
        order.save(update_fields=["checkout_session_id"])
        return JsonResponse({"id": session.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=webhook_secret
            )
        else:
            event = json.loads(payload.decode("utf-8"))
    except Exception as e:
        return JsonResponse({"error": f"invalid payload: {e}"}, status=400)

    event_type = event.get("type") if isinstance(event, dict) else event["type"]
    data_object = (
        event.get("data", {}).get("object", {})
        if isinstance(event, dict)
        else event["data"]["object"]
    )

    if event_type == "checkout.session.completed":
        session_id = data_object.get("id")
        if session_id:
            try:
                order = Order.objects.get(checkout_session_id=session_id)
                if not order.paid:
                    order.paid = True
                    order.save(update_fields=["paid"])
            except Order.DoesNotExist:
                pass

    return JsonResponse({"status": "ok"})


@require_http_methods(["POST", "GET"])
def create_order(request):
    currency = (
        request.GET.get("currency") or request.POST.get("currency") or "eur"
    ).lower()
    order = Order.objects.create(currency=currency)
    return redirect("order_detail", order_id=order.id)


@require_http_methods(["POST", "GET"])
@transaction.atomic
def add_to_order(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)
    try:
        item_id = int(request.GET.get("item_id") or request.POST.get("item_id"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "item_id is required"}, status=400)

    qty = int(request.GET.get("qty") or request.POST.get("qty") or 1)
    if qty < 1:
        qty = 1

    item = get_object_or_404(Item, pk=item_id)

    oi, created = OrderItem.objects.get_or_create(
        order=order, item=item, defaults={"quantity": qty}
    )
    if not created:
        oi.quantity += qty
        oi.save(update_fields=["quantity"])

    return redirect("order_detail", order_id=order.id)


@require_http_methods(["GET"])
def add_to_order_any(request):
    try:
        order_id = int(request.GET.get("order_id"))
        item_id = int(request.GET.get("item_id"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "order_id and item_id are required"}, status=400)

    qty = int(request.GET.get("qty") or 1)
    if qty < 1:
        qty = 1

    order = get_object_or_404(Order, pk=order_id)
    item = get_object_or_404(Item, pk=item_id)

    oi, created = OrderItem.objects.get_or_create(
        order=order, item=item, defaults={"quantity": qty}
    )
    if not created:
        oi.quantity += qty
        oi.save(update_fields=["quantity"])

    return redirect("order_detail", order_id=order.id)


@require_http_methods(["GET"])
def set_order_currency(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)
    cur = (request.GET.get("currency") or "").lower()
    if cur not in ("eur", "usd"):
        return JsonResponse({"error": "currency must be eur or usd"}, status=400)

    order.currency = cur
    order.save(update_fields=["currency"])
    return redirect("order_detail", order_id=order.id)
