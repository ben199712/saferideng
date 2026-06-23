from datetime import date

from django import forms

from .models import Vehicle


class VehicleRegistrationForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "plate_number",
            "vehicle_type",
            "vehicle_make",
            "vehicle_model",
            "vehicle_color",
            "year",
            "registered_route",
            "insurance_number",
        ]
        widgets = {
            "plate_number": forms.TextInput(attrs={"class": "w-full", "autocomplete": "off", "placeholder": "ABC-123-XY"}),
            "vehicle_type": forms.Select(attrs={"class": "w-full"}),
            "vehicle_make": forms.TextInput(attrs={"class": "w-full", "autocomplete": "organization"}),
            "vehicle_model": forms.TextInput(attrs={"class": "w-full"}),
            "vehicle_color": forms.TextInput(attrs={"class": "w-full"}),
            "year": forms.NumberInput(attrs={"class": "w-full", "min": 1900, "max": date.today().year + 1}),
            "registered_route": forms.TextInput(attrs={"class": "w-full", "placeholder": "Example: Airport - City Centre"}),
            "insurance_number": forms.TextInput(attrs={"class": "w-full", "autocomplete": "off"}),
        }

    def clean_plate_number(self):
        return self.cleaned_data["plate_number"].upper().replace(" ", "-")
