from django import forms

from .models import DriverProfile


class DriverProfileForm(forms.ModelForm):
    class Meta:
        model = DriverProfile
        fields = [
            "license_number",
            "vehicle_make",
            "vehicle_model",
            "vehicle_plate_number",
        ]
        widgets = {
            "license_number": forms.TextInput(attrs={"class": "w-full"}),
            "vehicle_make": forms.TextInput(attrs={"class": "w-full"}),
            "vehicle_model": forms.TextInput(attrs={"class": "w-full"}),
            "vehicle_plate_number": forms.TextInput(attrs={"class": "w-full"}),
        }


class DriverRegistrationForm(forms.Form):
    # Single-step driver registration form.

    license_number = forms.CharField(max_length=64, required=True)
    vehicle_make = forms.CharField(max_length=80, required=True)
    vehicle_model = forms.CharField(max_length=80, required=True)
    vehicle_plate_number = forms.CharField(max_length=20, required=True)

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        if instance is not None:
            for field_name in self.fields:
                self.initial[field_name] = getattr(instance, field_name)

    def to_model_payload(self):
        return {
            "license_number": self.cleaned_data["license_number"],
            "vehicle_make": self.cleaned_data["vehicle_make"],
            "vehicle_model": self.cleaned_data["vehicle_model"],
            "vehicle_plate_number": self.cleaned_data["vehicle_plate_number"],
        }

