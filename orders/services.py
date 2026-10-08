from django.db import transaction

from catalog.models import Product

from .models import OrderItem


class OutOfStock(Exception):
    """Raised when inventory moved underneath the shopper mid-checkout."""

    def __init__(self, product_name, available):
        self.product_name = product_name
        self.available = available
        super().__init__(f"Only {available} left of {product_name}.")


@transaction.atomic
def place_order(order, cart):
    """Persist the order, snapshot line prices and decrement stock atomically.

    Products are locked with select_for_update so two shoppers checking out the
    last unit cannot both succeed.
    """
    lines = list(cart)
    if not lines:
        raise ValueError("Cannot place an order with an empty cart.")

    product_ids = [line["product"].pk for line in lines]
    locked = Product.objects.select_for_update().in_bulk(product_ids)

    for line in lines:
        product = locked[line["product"].pk]
        if product.stock < line["quantity"]:
            raise OutOfStock(product.name, product.stock)

    order.save()

    items = []
    for line in lines:
        product = locked[line["product"].pk]
        product.stock -= line["quantity"]
        product.save(update_fields=["stock"])
        items.append(
            OrderItem(
                order=order,
                product=product,
                price=line["price"],
                quantity=line["quantity"],
            )
        )
    OrderItem.objects.bulk_create(items)

    cart.clear()
    return order
