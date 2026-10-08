from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.urls import reverse

from catalog.models import Category, Product

from .cart import Cart


def _request_with_session(rf):
    from django.contrib.sessions.middleware import SessionMiddleware

    request = rf.get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    return request


class CartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Audio", slug="audio")
        cls.headphones = Product.objects.create(
            category=category,
            name="Studio Headphones",
            slug="studio-headphones",
            price=Decimal("199.00"),
            stock=5,
        )
        cls.mic = Product.objects.create(
            category=category,
            name="Desk Mic",
            slug="desk-mic",
            price=Decimal("129.50"),
            stock=2,
        )

    def setUp(self):
        self.cart = Cart(_request_with_session(RequestFactory()))

    def test_new_cart_is_empty(self):
        self.assertEqual(len(self.cart), 0)
        self.assertEqual(self.cart.get_total_price(), Decimal("0.00"))

    def test_add_accumulates_quantity_for_same_product(self):
        self.cart.add(self.headphones, quantity=2)
        self.cart.add(self.headphones, quantity=1)
        self.assertEqual(len(self.cart), 3)

    def test_override_quantity_replaces_rather_than_adds(self):
        self.cart.add(self.headphones, quantity=3)
        self.cart.add(self.headphones, quantity=1, override_quantity=True)
        self.assertEqual(len(self.cart), 1)

    def test_quantity_is_capped_at_available_stock(self):
        self.cart.add(self.mic, quantity=10)
        self.assertEqual(len(self.cart), 2)

    def test_total_price_sums_line_items(self):
        self.cart.add(self.headphones, quantity=2)
        self.cart.add(self.mic, quantity=1)
        self.assertEqual(self.cart.get_total_price(), Decimal("527.50"))

    def test_price_is_snapshotted_at_add_time(self):
        self.cart.add(self.headphones, quantity=1)
        self.headphones.price = Decimal("249.00")
        self.headphones.save()
        self.assertEqual(self.cart.get_total_price(), Decimal("199.00"))

    def test_remove_drops_the_line_item(self):
        self.cart.add(self.headphones, quantity=1)
        self.cart.remove(self.headphones)
        self.assertEqual(len(self.cart), 0)

    def test_override_to_zero_removes_the_line_item(self):
        self.cart.add(self.headphones, quantity=2)
        self.cart.add(self.headphones, quantity=0, override_quantity=True)
        self.assertEqual(len(self.cart), 0)

    def test_clear_empties_the_cart(self):
        self.cart.add(self.headphones, quantity=2)
        self.cart.add(self.mic, quantity=1)
        self.cart.clear()
        self.assertEqual(len(self.cart), 0)

    def test_iteration_yields_product_and_line_total(self):
        self.cart.add(self.headphones, quantity=2)
        (line,) = list(self.cart)
        self.assertEqual(line["product"], self.headphones)
        self.assertEqual(line["quantity"], 2)
        self.assertEqual(line["total_price"], Decimal("398.00"))


class CartViewTests(TestCase):
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

    def test_add_redirects_to_cart_and_stores_the_item(self):
        response = self.client.post(
            reverse("cart:cart_add", args=[self.product.pk]),
            {"quantity": 2, "override": ""},
        )
        self.assertRedirects(response, reverse("cart:cart_detail"))
        self.assertEqual(self.client.session["cart"][str(self.product.pk)]["quantity"], 2)

    def test_add_rejects_invalid_quantity(self):
        response = self.client.post(
            reverse("cart:cart_add", args=[self.product.pk]),
            {"quantity": 0, "override": ""},
        )
        self.assertRedirects(response, self.product.get_absolute_url())
        self.assertNotIn(str(self.product.pk), self.client.session.get("cart", {}))

    def test_add_rejects_out_of_stock_product(self):
        self.product.stock = 0
        self.product.save()
        response = self.client.post(
            reverse("cart:cart_add", args=[self.product.pk]), {"quantity": 1}
        )
        self.assertRedirects(response, self.product.get_absolute_url())
        self.assertNotIn(str(self.product.pk), self.client.session.get("cart", {}))

    def test_add_requires_post(self):
        response = self.client.get(reverse("cart:cart_add", args=[self.product.pk]))
        self.assertEqual(response.status_code, 405)

    def test_remove_clears_the_item(self):
        self.client.post(
            reverse("cart:cart_add", args=[self.product.pk]), {"quantity": 1}
        )
        self.client.post(reverse("cart:cart_remove", args=[self.product.pk]))
        self.assertEqual(self.client.session["cart"], {})

    def test_cart_detail_renders_empty_state(self):
        response = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your cart is empty")
