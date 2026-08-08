from django import forms
from django.forms.widgets import TextInput

from .models import EmergencyContact, SOSAuthorityContact


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ["full_name", "phone_number", "relationship"]
        widgets = {
            "full_name": TextInput(attrs={"class": "w-full", "autocomplete": "name"}),
            "phone_number": TextInput(attrs={"class": "w-full", "autocomplete": "tel", "type": "tel"}),
            "relationship": TextInput(attrs={"class": "w-full", "placeholder": "Family, Friend, Colleague"}),
        }

    def clean_full_name(self):
        return self.cleaned_data["full_name"].strip()

    def clean_phone_number(self):
        return self.cleaned_data["phone_number"].strip()

    def clean_relationship(self):
        return self.cleaned_data["relationship"].strip()


class SOSAuthorityContactForm(forms.ModelForm):
    class Meta:
        model = SOSAuthorityContact
        fields = ["authority_name", "official_email", "sms_phone_number", "physical_jurisdiction", "is_active"]
        widgets = {
            "authority_name": TextInput(attrs={"class": "w-full"}),
            "official_email": TextInput(attrs={"class": "w-full", "type": "email", "autocomplete": "email"}),
            "sms_phone_number": TextInput(attrs={"class": "w-full", "type": "tel", "autocomplete": "tel"}),
            "physical_jurisdiction": TextInput(attrs={"class": "w-full"}),
        }

    def clean_authority_name(self):
        return (self.cleaned_data["authority_name"] or "").strip()

    def clean_official_email(self):
        return (self.cleaned_data["official_email"] or "").strip()

    def clean_sms_phone_number(self):
        return (self.cleaned_data["sms_phone_number"] or "").strip()

    def clean_physical_jurisdiction(self):
        return (self.cleaned_data["physical_jurisdiction"] or "").strip()
