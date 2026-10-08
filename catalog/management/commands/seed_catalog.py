from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product

CATALOG = {
    "Audio": [
        ("Studio Headphones", "Closed-back reference monitors for long sessions.", "199.00", 12),
        ("Desk Microphone", "Cardioid USB condenser with a shock mount.", "129.50", 7),
        ("Bookshelf Speakers", "Two-way powered pair with optical input.", "349.00", 4),
    ],
    "Desk": [
        ("Task Lamp", "Dimmable LED arm lamp with adjustable colour temperature.", "59.00", 20),
        ("Monitor Stand", "Solid oak riser with a cable channel.", "84.00", 9),
        ("Laptop Dock", "Single-cable dock with dual display output.", "219.00", 0),
    ],
    "Peripherals": [
        ("Mechanical Keyboard", "Hot-swappable 75% board with PBT keycaps.", "149.00", 15),
        ("Vertical Mouse", "Ergonomic wireless mouse with six buttons.", "69.00", 11),
        ("Palm Rest", "Walnut wrist rest sized for compact boards.", "39.00", 25),
    ],
}


class Command(BaseCommand):
    help = "Populate the catalog with demo categories and products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing catalog rows before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            Product.objects.all().delete()
            Category.objects.all().delete()

        created = 0
        for category_name, products in CATALOG.items():
            category, _ = Category.objects.get_or_create(
                name=category_name, defaults={"slug": slugify(category_name)}
            )
            for name, description, price, stock in products:
                _, made = Product.objects.get_or_create(
                    slug=slugify(name),
                    defaults={
                        "category": category,
                        "name": name,
                        "description": description,
                        "price": Decimal(price),
                        "stock": stock,
                    },
                )
                created += int(made)

        self.stdout.write(
            self.style.SUCCESS(f"Catalog seeded ({created} new products).")
        )


def slugify(value):
    from django.utils.text import slugify as django_slugify

    return django_slugify(value)
