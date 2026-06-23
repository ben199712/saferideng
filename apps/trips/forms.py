from django import forms

from .models import Trip


class TripStartForm(forms.Form):
    passenger_name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "w-full", "autocomplete": "name"}))
    passenger_phone = forms.CharField(max_length=30, widget=forms.TelInput(attrs={"class": "w-full", "autocomplete": "tel"}))
    destination = forms.CharField(max_length=160, widget=forms.TextInput(attrs={"class": "w-full", "placeholder": "Where are you going?"}))
    start_location = forms.CharField(max_length=160, required=False, widget=forms.TextInput(attrs={"class": "w-full", "placeholder": "Pickup location"}))

    def clean_passenger_name(self):
        return self.cleaned_data["passenger_name"].strip()

    def clean_passenger_phone(self):
        return self.cleaned_data["passenger_phone"].strip()

    def clean_destination(self):
        return self.cleaned_data["destination"].strip()

    def clean_start_location(self):
        value = self.cleaned_data.get("start_location", "").strip()
        return value


class TripEndForm(forms.Form):
    confirm = forms.BooleanField(required=True)
