from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class ProductModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Audio", slug="audio")

    def _product(self, **kwargs):
        defaults = {
            "category": self.category,
            "name": "Studio Headphones",
            "slug": "studio-headphones",
            "price": Decimal("199.00"),
            "stock": 5,
        }
        return Product.objects.create(**{**defaults, **kwargs})

    def test_in_stock_is_true_for_active_product_with_stock(self):
        self.assertTrue(self._product().in_stock)

    def test_in_stock_is_false_when_stock_is_zero(self):
        self.assertFalse(self._product(stock=0).in_stock)

    def test_in_stock_is_false_when_inactive(self):
        self.assertFalse(self._product(is_active=False).in_stock)

    def test_available_queryset_excludes_inactive_and_sold_out(self):
        live = self._product()
        self._product(name="Sold out", slug="sold-out", stock=0)
        self._product(name="Hidden", slug="hidden", is_active=False)

        self.assertQuerySetEqual(Product.objects.available(), [live])

    def test_search_matches_name_and_description(self):
        match = self._product(description="Over-ear reference monitors")
        self._product(name="Cable", slug="cable", description="3.5mm")

        self.assertQuerySetEqual(Product.objects.search("reference"), [match])
        self.assertQuerySetEqual(Product.objects.search("headphones"), [match])

    def test_search_with_blank_term_returns_everything(self):
        self._product()
        self.assertEqual(Product.objects.search("").count(), 1)


class CatalogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.audio = Category.objects.create(name="Audio", slug="audio")
        cls.desk = Category.objects.create(name="Desk", slug="desk")
        cls.headphones = Product.objects.create(
            category=cls.audio,
            name="Studio Headphones",
            slug="studio-headphones",
            price=Decimal("199.00"),
            stock=5,
        )
        cls.lamp = Product.objects.create(
            category=cls.desk,
            name="Task Lamp",
            slug="task-lamp",
            price=Decimal("59.00"),
            stock=3,
        )

    def test_product_list_renders_all_available_products(self):
        response = self.client.get(reverse("catalog:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Studio Headphones")
        self.assertContains(response, "Task Lamp")

    def test_product_list_filters_by_category(self):
        response = self.client.get(
            reverse("catalog:product_list_by_category", args=["audio"])
        )
        self.assertContains(response, "Studio Headphones")
        self.assertNotContains(response, "Task Lamp")

    def test_product_list_filters_by_search_term(self):
        response = self.client.get(reverse("catalog:product_list"), {"q": "lamp"})
        self.assertContains(response, "Task Lamp")
        self.assertNotContains(response, "Studio Headphones")

    def test_unknown_category_returns_404(self):
        response = self.client.get(
            reverse("catalog:product_list_by_category", args=["nope"])
        )
        self.assertEqual(response.status_code, 404)

    def test_product_detail_shows_related_products_from_same_category(self):
        sibling = Product.objects.create(
            category=self.audio,
            name="Desk Mic",
            slug="desk-mic",
            price=Decimal("129.00"),
            stock=2,
        )
        response = self.client.get(self.headphones.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["related_products"], [sibling])

    def test_product_detail_404s_for_inactive_product(self):
        self.lamp.is_active = False
        self.lamp.save()
        self.assertEqual(self.client.get(self.lamp.get_absolute_url()).status_code, 404)
