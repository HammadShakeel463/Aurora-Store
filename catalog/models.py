from decimal import Decimal

from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:product_list_by_category", args=[self.slug])


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.filter(is_active=True, stock__gt=0)

    def search(self, term):
        if not term:
            return self
        return self.filter(
            models.Q(name__icontains=term) | models.Q(description__icontains=term)
        )


class Product(models.Model):
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.PROTECT
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "stock"]),
            models.Index(fields=["category", "name"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=Decimal("0.00")),
                name="product_price_non_negative",
            )
        ]

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.is_active and self.stock > 0

    def get_absolute_url(self):
        return reverse("catalog:product_detail", args=[self.slug])
