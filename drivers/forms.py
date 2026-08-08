from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User

from .constants import COUNTRY_CHOICES, GENDER_CHOICES, STATE_CHOICES, TRANSPORT_UNION_CHOICES, get_state_lga_mapping
from .documents import DOCUMENT_REQUIREMENTS
from .models import DriverDocument, DriverProfile
from .validators import (
    validate_driver_age,
    validate_e164_phone_number,
    validate_nin,
    validate_residential_address,
    validate_state_lga_pair,
    validate_union_membership_number,
    validate_driver_license_number,
    validate_driver_email,
)


def _normalize_lga_key(key):
    return (
        str(key or "")
        .strip()
        .lower()
        .replace("-", " ")
        .replace("–", " ")
        .replace("—", " ")
        .replace("\t", " ")
    )


def _resolve_lgas_for_state(state_candidate):
    """Resolve LGAs for a potentially-un-normalized state string.

    Uses the same normalization + fuzzy logic as the client-side JavaScript
    resolver so client values always match server-side mapping.
    """
    if not state_candidate:
        return []
    mapping = get_state_lga_mapping()
    norm_candidate = _normalize_lga_key(state_candidate)

    # 1) exact match
    if state_candidate in mapping:
        return list(mapping[state_candidate])
    # 2) normalized exact match
    flat_map = {}
    for k, v in mapping.items():
        flat_map[_normalize_lga_key(k)] = list(v)
    if norm_candidate in flat_map:
        return flat_map[norm_candidate]
    # 3) startsWith / endsWith
    for key in mapping:
        k = _normalize_lga_key(key)
        if k.startswith(norm_candidate) or norm_candidate.startswith(k):
            return list(mapping[key])
    # 4) token subset match
    tokens = [t for t in norm_candidate.split(" ") if t]
    if tokens:
        for key in mapping:
            k_tokens = [t for t in _normalize_lga_key(key).split(" ") if t]
            if k_tokens and all(t in k_tokens for t in tokens):
                return list(mapping[key])
    return []


class DriverProfileForm(forms.ModelForm):
    class Meta:
        model = DriverProfile
        fields = [
            "date_of_birth",
            "gender",
            "phone_number",
            "alternative_phone_number",
            "email",
            "residential_address",
            "state",
            "lga",
            "nationality",
            "nin",
            "license_number",
            "driver_license_expiry_date",
            "transport_union",
            "union_membership_number",
            "years_of_driving_experience",
            "vehicle_make",
            "vehicle_model",
            "vehicle_plate_number",
        ]


class DriverRegistrationForm(DriverProfileForm):
    class Meta(DriverProfileForm.Meta):
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"class": "w-full", "type": "date", "required": True}),
            "gender": forms.Select(attrs={"class": "w-full", "required": True}, choices=GENDER_CHOICES),
            "phone_number": forms.TextInput(attrs={"class": "w-full", "autocomplete": "tel", "placeholder": "+2348012345678", "pattern": r"^\+[1-9]\d{7,14}$", "required": True}),
            "alternative_phone_number": forms.TextInput(attrs={"class": "w-full", "autocomplete": "tel", "placeholder": "+2348098765432", "pattern": r"^\+[1-9]\d{7,14}$"}),
            "email": forms.EmailInput(attrs={"class": "w-full", "autocomplete": "email", "required": True}),
            "residential_address": forms.Textarea(attrs={"class": "w-full", "rows": 3, "minlength": 10, "required": True}),
            "state": forms.Select(attrs={"class": "w-full", "required": True, "data-state-field": "1", "autocomplete": "address-level1"}, choices=(("", "Select state"),) + STATE_CHOICES),
            "lga": forms.Select(attrs={"class": "w-full", "required": True, "data-lga-field": "1", "autocomplete": "address-level2", "data-state": "awaiting-state", "aria-label": "Local Government Area"}),
            "nationality": forms.Select(attrs={"class": "w-full", "required": True, "autocomplete": "country"}, choices=(("", "Select nationality"),) + COUNTRY_CHOICES),
            "nin": forms.TextInput(attrs={"class": "w-full", "autocomplete": "off", "inputmode": "numeric", "pattern": r"^\d{11}$", "maxlength": 11, "required": True}),
            "license_number": forms.TextInput(attrs={"class": "w-full", "autocomplete": "off", "placeholder": "Enter FRSC license number", "required": True}),
            "driver_license_expiry_date": forms.DateInput(attrs={"class": "w-full", "type": "date", "required": True}),
            "transport_union": forms.Select(attrs={"class": "w-full", "required": True}, choices=(("", "Select union"),) + TRANSPORT_UNION_CHOICES),
            "union_membership_number": forms.TextInput(attrs={"class": "w-full", "autocomplete": "off", "required": True}),
            "years_of_driving_experience": forms.NumberInput(attrs={"class": "w-full", "min": 2, "max": 70, "required": True}),
            "vehicle_make": forms.TextInput(attrs={"class": "w-full", "required": True}),
            "vehicle_model": forms.TextInput(attrs={"class": "w-full", "required": True}),
            "vehicle_plate_number": forms.TextInput(attrs={"class": "w-full", "autocomplete": "off", "placeholder": "ABC-123-XY", "required": True}),
        }

    required_fields = (
        "date_of_birth",
        "gender",
        "phone_number",
        "email",
        "residential_address",
        "state",
        "lga",
        "nationality",
        "nin",
        "license_number",
        "driver_license_expiry_date",
        "transport_union",
        "union_membership_number",
        "years_of_driving_experience",
        "vehicle_make",
        "vehicle_model",
        "vehicle_plate_number",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        for field_name in self.required_fields:
            self.fields[field_name].required = True

        if self.user and not self.initial.get("email"):
            self.initial["email"] = self.user.email
        if self.user and not self.initial.get("phone_number"):
            self.initial["phone_number"] = self.user.phone_number

        selected_state = self.data.get("state") or self.initial.get("state") or getattr(self.instance, "state", "")
        lgas_for_state = _resolve_lgas_for_state(selected_state)
        # Ensure the submitted/instance/initial LGA value — even if mapping lookup failed but string was
        # a different but equivalent, coerce valid lgas_for_state
        lga_choices = [("", "Select LGA")]
        if lgas_for_state:
            lga_choices.extend((value, value) for value in lgas_for_state)
        # Make sure the current LGA value is always a valid choice (even if
        # state fuzzy-resolver didn't pick it up on re-renders)
        submitted_lga = (
            (self.data.get("lga") if hasattr(self, "data") else "")
            or self.initial.get("lga")
            or getattr(self.instance, "lga", "")
            or ""
        ).strip()
        submitted_lga_choices = {value for _, value in lga_choices}
        if submitted_lga and submitted_lga not in submitted_lga_choices:
            lga_choices.append((submitted_lga, submitted_lga))
        self.fields["lga"].choices = lga_choices

    def clean_phone_number(self):
        value = (self.cleaned_data["phone_number"] or "").strip()
        validate_e164_phone_number(value)
        return value

    def clean_alternative_phone_number(self):
        value = (self.cleaned_data.get("alternative_phone_number") or "").strip()
        if value:
            validate_e164_phone_number(value)
        return value or None

    def clean_email(self):
        value = (self.cleaned_data["email"] or "").strip().lower()
        validate_driver_email(value)
        qs = User.objects.exclude(pk=getattr(self.user, "pk", None)).filter(email__iexact=value)
        if qs.exists():
            raise ValidationError("This email address is already in use by another account.")
        return value

    def clean_residential_address(self):
        value = (self.cleaned_data["residential_address"] or "").strip()
        validate_residential_address(value)
        return value

    def clean_nin(self):
        value = (self.cleaned_data["nin"] or "").strip()
        validate_nin(value)
        return value

    def clean_license_number(self):
        value = (self.cleaned_data["license_number"] or "").strip().upper().replace(" ", "")
        validate_driver_license_number(value)
        return value

    def clean_union_membership_number(self):
        value = (self.cleaned_data["union_membership_number"] or "").strip().upper()
        validate_union_membership_number(value)
        return value

    def clean_vehicle_plate_number(self):
        return (self.cleaned_data["vehicle_plate_number"] or "").strip().upper().replace(" ", "-")

    def clean_date_of_birth(self):
        value = self.cleaned_data.get("date_of_birth")
        validate_driver_age(value)
        return value

    def clean_lga(self):
        return (self.cleaned_data.get("lga") or "").strip()

    def clean(self):
        cleaned_data = super().clean()
        state = (cleaned_data.get("state") or self.data.get("state") or getattr(self.instance, "state") or "").strip()
        lga = (cleaned_data.get("lga") or self.data.get("lga") or "").strip()
        if not lga and state:
            # try to recover if cleaned_data lost lga due to field-specific required but lga was in post
            self.add_error("lga", "Select an LGA for the chosen state.")
        elif state and lga:
            try:
                validate_state_lga_pair(state, lga)
            except ValidationError as validation_fallback:
                # Last resort: fuzzy-resolve state and compare lga against resolved list
                lgas = _resolve_lgas_for_state(state)
                normalized_lgas = {_normalize_lga_key(v) for v in lgas}
                if _normalize_lga_key(lga) not in normalized_lgas:
                    for error in validation_fallback.error_list:
                        self.add_error("lga", error.message)
        return cleaned_data


class DriverDocumentUploadForm(forms.Form):
    document_type = forms.ChoiceField(choices=DriverDocument.DocumentType.choices)
    file = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs.update(
            {
                "accept": ".jpg,.jpeg,.png,.webp,.pdf",
            }
        )

    def clean_document_type(self):
        value = self.cleaned_data["document_type"]
        if value not in DOCUMENT_REQUIREMENTS:
            raise ValidationError("Invalid document type selected.")
        return value

