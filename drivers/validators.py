import re
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from .constants import get_state_lga_mapping


E164_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")
NIN_REGEX = re.compile(r"^\d{11}$")
LICENSE_REGEX = re.compile(r"^[A-Z0-9-]{8,20}$")
UNION_MEMBERSHIP_REGEX = re.compile(r"^[A-Z0-9/-]{5,30}$")


def validate_driver_age(value):
    if not value:
        return
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 21:
        raise ValidationError("Drivers must be at least 21 years old.")


def validate_e164_phone_number(value):
    if not value:
        return
    if not E164_REGEX.match(value):
        raise ValidationError("Use an international phone number in E.164 format, for example +2348012345678.")


def validate_driver_email(value):
    if not value:
        return
    EmailValidator(message="Enter a valid email address.")(value)


def validate_nin(value):
    if not value:
        return
    if not NIN_REGEX.match(value):
        raise ValidationError("NIN must contain exactly 11 digits.")


def validate_driver_license_number(value):
    if not value:
        return
    if not LICENSE_REGEX.match(value):
        raise ValidationError("Enter a valid driver license number using 8 to 20 uppercase letters, digits, or hyphens.")


def validate_residential_address(value):
    if not value:
        return
    if len(value.strip()) < 10:
        raise ValidationError("Residential address must be at least 10 characters long.")


def validate_union_membership_number(value):
    if not value:
        return
    if not UNION_MEMBERSHIP_REGEX.match(value):
        raise ValidationError("Enter a valid transport union membership number.")


def validate_state_lga_pair(state, lga):
    if not state or not lga:
        return
    choices = get_state_lga_mapping().get(state)
    if choices and lga not in choices:
        raise ValidationError("Select a valid LGA for the chosen state.")
