from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart

from .forms import OrderCreateForm
from .models import Order
from .services import OutOfStock, place_order


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, "Your cart is empty.")
        return redirect("catalog:product_list")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                order = place_order(form.save(commit=False), cart)
            except OutOfStock as exc:
                messages.error(request, str(exc))
                return redirect("cart:cart_detail")
            return redirect("orders:order_created", reference=order.reference)
    else:
        form = OrderCreateForm()

    return render(request, "orders/checkout.html", {"form": form})


def order_created(request, reference):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"), reference=reference
    )
    return render(request, "orders/created.html", {"order": order})
