from decimal import Decimal

from django.conf import settings

from catalog.models import Product


class Cart:
    """A session-backed shopping cart.

    Line items are stored as {product_id: {"quantity": int, "price": str}} so the
    price the shopper saw is captured at add-time rather than re-read on render.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_KEY)
        if cart is None:
            cart = self.session[settings.CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        key = str(product.pk)
        if key not in self.cart:
            self.cart[key] = {"quantity": 0, "price": str(product.price)}
        if override_quantity:
            self.cart[key]["quantity"] = quantity
        else:
            self.cart[key]["quantity"] += quantity

        if self.cart[key]["quantity"] <= 0:
            self.remove(product)
        else:
            # Never let the cart promise more units than inventory holds.
            self.cart[key]["quantity"] = min(self.cart[key]["quantity"], product.stock)
            self.save()

    def remove(self, product):
        self.cart.pop(str(product.pk), None)
        self.save()

    def clear(self):
        self.session[settings.CART_SESSION_KEY] = {}
        self.cart = self.session[settings.CART_SESSION_KEY]
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        products = Product.objects.filter(pk__in=self.cart.keys()).select_related(
            "category"
        )
        for product in products:
            item = self.cart[str(product.pk)]
            price = Decimal(item["price"])
            yield {
                "product": product,
                "quantity": item["quantity"],
                "price": price,
                "total_price": price * item["quantity"],
            }

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            (Decimal(item["price"]) * item["quantity"] for item in self.cart.values()),
            Decimal("0.00"),
        )
