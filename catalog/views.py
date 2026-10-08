from django.core.paginator import Paginator
from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request, category_slug=None):
    """Paginated catalog, optionally narrowed by category and a search term."""
    category = None
    products = Product.objects.available().select_related("category")

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get("q", "").strip()
    products = products.search(query)

    page = Paginator(products, settings.PRODUCTS_PER_PAGE).get_page(
        request.GET.get("page")
    )
    return render(
        request,
        "catalog/product_list.html",
        {
            "category": category,
            "categories": Category.objects.all(),
            "page_obj": page,
            "query": query,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"), slug=slug, is_active=True
    )
    related = (
        Product.objects.available()
        .filter(category=product.category)
        .exclude(pk=product.pk)[:3]
    )
    return render(
        request,
        "catalog/product_detail.html",
        {"product": product, "related_products": related},
    )
