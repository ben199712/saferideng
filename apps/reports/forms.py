from django import forms

from .models import IncidentReport


class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = ["report_type", "description"]
        widgets = {
            "report_type": forms.Select(attrs={"class": "w-full"}),
            "description": forms.Textarea(attrs={"class": "w-full", "rows": 6, "placeholder": "Describe what happened"}),
        }

    def clean_description(self):
        return self.cleaned_data["description"].strip()
