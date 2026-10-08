from django import forms


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=20, initial=1)
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)
