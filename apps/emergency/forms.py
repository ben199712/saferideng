from django import forms

from .models import EmergencyContact


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ["full_name", "phone_number", "relationship"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "w-full", "autocomplete": "name"}),
            "phone_number": forms.TelInput(attrs={"class": "w-full", "autocomplete": "tel"}),
            "relationship": forms.TextInput(attrs={"class": "w-full", "placeholder": "Family, Friend, Colleague"}),
        }

    def clean_full_name(self):
        return self.cleaned_data["full_name"].strip()

    def clean_phone_number(self):
        return self.cleaned_data["phone_number"].strip()

    def clean_relationship(self):
        return self.cleaned_data["relationship"].strip()
