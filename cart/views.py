from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product

from .cart import Cart
from .forms import AddToCartForm


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    form = AddToCartForm(request.POST)

    if not form.is_valid():
        messages.error(request, "Please enter a quantity between 1 and 20.")
        return redirect(product.get_absolute_url())

    if not product.in_stock:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect(product.get_absolute_url())

    cart.add(
        product=product,
        quantity=form.cleaned_data["quantity"],
        override_quantity=form.cleaned_data["override"],
    )
    messages.success(request, f"{product.name} added to your cart.")
    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, pk=product_id)
    cart.remove(product)
    messages.info(request, f"{product.name} removed from your cart.")
    return redirect("cart:cart_detail")


def cart_detail(request):
    return render(request, "cart/detail.html", {"update_form": AddToCartForm})
