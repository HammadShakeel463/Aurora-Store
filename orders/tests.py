from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.urls import reverse

from cart.cart import Cart
from catalog.models import Category, Product

from .models import Order, OrderItem
from .services import OutOfStock, place_order


def _cart():
    from django.contrib.sessions.middleware import SessionMiddleware

    request = RequestFactory().get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    return Cart(request)


class PlaceOrderTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Audio", slug="audio")
        self.headphones = Product.objects.create(
            category=category,
            name="Studio Headphones",
            slug="studio-headphones",
            price=Decimal("199.00"),
            stock=5,
        )
        self.mic = Product.objects.create(
            category=category,
            name="Desk Mic",
            slug="desk-mic",
            price=Decimal("129.50"),
            stock=2,
        )
        self.cart = _cart()

    def _order(self):
        return Order(
            first_name="Hammad",
            last_name="Shakeel",
            email="buyer@example.com",
            address="12 Example Road",
            city="Karachi",
            postal_code="75500",
        )

    def test_order_creates_line_items_and_decrements_stock(self):
        self.cart.add(self.headphones, quantity=2)
        self.cart.add(self.mic, quantity=1)

        order = place_order(self._order(), self.cart)

        self.assertEqual(order.items.count(), 2)
        self.headphones.refresh_from_db()
        self.mic.refresh_from_db()
        self.assertEqual(self.headphones.stock, 3)
        self.assertEqual(self.mic.stock, 1)

    def test_order_total_matches_the_cart(self):
        self.cart.add(self.headphones, quantity=2)
        self.cart.add(self.mic, quantity=1)
        order = place_order(self._order(), self.cart)
        self.assertEqual(order.get_total_cost(), Decimal("527.50"))

    def test_line_price_is_snapshotted_not_re_read(self):
        self.cart.add(self.headphones, quantity=1)
        self.headphones.price = Decimal("249.00")
        self.headphones.save()

        order = place_order(self._order(), self.cart)
        self.assertEqual(order.items.get().price, Decimal("199.00"))

    def test_cart_is_emptied_after_a_successful_order(self):
        self.cart.add(self.headphones, quantity=1)
        place_order(self._order(), self.cart)
        self.assertEqual(len(self.cart), 0)

    def test_reference_is_generated_and_unique(self):
        self.cart.add(self.headphones, quantity=1)
        first = place_order(self._order(), self.cart)

        self.cart.add(self.mic, quantity=1)
        second = place_order(self._order(), self.cart)

        self.assertTrue(first.reference)
        self.assertNotEqual(first.reference, second.reference)

    def test_empty_cart_is_rejected(self):
        with self.assertRaises(ValueError):
            place_order(self._order(), self.cart)

    def test_insufficient_stock_raises_and_writes_nothing(self):
        self.cart.add(self.mic, quantity=2)
        # Inventory moves underneath the shopper after the cart was filled.
        Product.objects.filter(pk=self.mic.pk).update(stock=1)

        with self.assertRaises(OutOfStock):
            place_order(self._order(), self.cart)

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.mic.refresh_from_db()
        self.assertEqual(self.mic.stock, 1)


class CheckoutViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Audio", slug="audio")
        cls.product = Product.objects.create(
            category=category,
            name="Studio Headphones",
            slug="studio-headphones",
            price=Decimal("199.00"),
            stock=5,
        )

    FORM = {
        "first_name": "Hammad",
        "last_name": "Shakeel",
        "email": "buyer@example.com",
        "address": "12 Example Road",
        "city": "Karachi",
        "postal_code": "75500",
    }

    def _fill_cart(self, quantity=1):
        self.client.post(
            reverse("cart:cart_add", args=[self.product.pk]), {"quantity": quantity}
        )

    def test_checkout_redirects_when_cart_is_empty(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(response, reverse("catalog:product_list"))

    def test_checkout_renders_the_form_for_a_filled_cart(self):
        self._fill_cart()
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delivery details")

    def test_valid_submission_creates_the_order_and_redirects(self):
        self._fill_cart(2)
        response = self.client.post(reverse("orders:checkout"), self.FORM)

        order = Order.objects.get()
        self.assertRedirects(
            response, reverse("orders:order_created", args=[order.reference])
        )
        self.assertEqual(order.items.get().quantity, 2)

    def test_invalid_submission_does_not_create_an_order(self):
        self._fill_cart()
        response = self.client.post(
            reverse("orders:checkout"), {**self.FORM, "email": "not-an-email"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_confirmation_page_shows_the_reference(self):
        self._fill_cart()
        self.client.post(reverse("orders:checkout"), self.FORM)
        order = Order.objects.get()

        response = self.client.get(
            reverse("orders:order_created", args=[order.reference])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.reference)

    def test_unknown_reference_returns_404(self):
        response = self.client.get(
            reverse("orders:order_created", args=["NOPE12345678"])
        )
        self.assertEqual(response.status_code, 404)
