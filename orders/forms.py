from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email", "address", "city", "postal_code"]
        widgets = {
            field: forms.TextInput(attrs={"class": "field"})
            for field in ["first_name", "last_name", "address", "city", "postal_code"]
        }
