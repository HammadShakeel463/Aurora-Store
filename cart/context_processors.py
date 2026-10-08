from .cart import Cart


def cart_summary(request):
    """Expose the cart to every template so the header badge always has a count."""
    cart = Cart(request)
    return {"cart": cart, "cart_item_count": len(cart)}
