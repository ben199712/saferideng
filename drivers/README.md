# Driver Profile Safety Upgrade

## Audit Summary

Before this upgrade, `drivers.DriverProfile` only stored:

- `license_number`
- `vehicle_make`
- `vehicle_model`
- `vehicle_plate_number`
- `verification_status`
- `is_approved`
- timestamps

Related usage points were:

- driver self-service registration and profile pages in `drivers/views.py`
- admin review in `drivers/admin.py`
- approval dashboard metrics in `dashboard/views.py`
- dashboard approval table in `dashboard/templates/dashboard/dashboard_home.html`

Key gaps found during the audit:

- no age, residency, union, or identity data
- no encryption for sensitive PII
- no E.164, NIN, license, or residency validation
- no state/LGA cascade support
- no license-expiry operational alerts
- no regression coverage for sensitive-field storage

## Added Fields

The upgraded `DriverProfile` now supports:

- `date_of_birth`: must be age 21+
- `gender`: `male`, `female`, `prefer_not_to_say`
- `phone_number`: encrypted, unique, indexed, E.164 validated
- `alternative_phone_number`: encrypted, optional, E.164 validated
- `email`: unique, indexed, synced to the account email
- `residential_address`: encrypted text, minimum length enforced
- `state`: indexed, validated against supported operating-region states
- `lga`: validated against the selected state
- `nationality`: country choice list
- `nin`: encrypted, unique, indexed, 11-digit validation
- `license_number`: encrypted, unique, indexed, FRSC-style format validation
- `driver_license_expiry_date`: indexed, used for 90-day expiry alerts
- `transport_union`: vetted transport union choice list
- `union_membership_number`: format validated
- `years_of_driving_experience`: range `2..70` and cross-checked against age

Legacy compatibility fields remain in place:

- `vehicle_make`
- `vehicle_model`
- `vehicle_plate_number`

These stay available so the current dashboard and driver profile screens continue to work while the separate vehicle workflow remains the primary operational record.

## Validation Rules

Server-side validation lives in `drivers/validators.py` and `drivers/models.py`.

- Age: minimum 21 years old
- Phone numbers: E.164 format such as `+2348012345678`
- Email: Django email validation plus uniqueness checks
- NIN: exactly 11 digits
- Driver license: 8 to 20 uppercase letters, digits, or hyphens
- Residential address: minimum 10 characters
- Union membership number: uppercase alphanumeric format with `/` or `-`
- State/LGA pair: selected LGA must belong to selected state
- Experience: minimum 2, maximum 70, and cannot exceed age-derived plausibility
- License expiry: must be a future date
- Alternative phone number: must differ from the primary phone number

Client-side validation is also present in `templates/drivers/driver_register.html` through:

- `type="date"`
- `type="email"`
- `pattern`
- `maxlength`
- `min` / `max`
- dynamic state-to-LGA dropdown population

## Encryption And Privacy

Sensitive PII is encrypted at rest using AES-SIV with a SHA-256 derived key from `DRIVER_PII_ENCRYPTION_KEY` or Django `SECRET_KEY`.

Encrypted fields:

- `phone_number`
- `alternative_phone_number`
- `residential_address`
- `nin`
- `license_number`

Implementation files:

- `drivers/crypto.py`
- `drivers/fields.py`

Operational notes:

- encrypted values are stored in the database with the `enc1:` prefix
- application code reads decrypted values transparently
- uniqueness is preserved because AES-SIV is deterministic for the same plaintext/key pair

## Workflow Changes

- Driver registration now uses a full `ModelForm` in `drivers/forms.py`
- Account email and phone number are synchronized from the approved registration data in `drivers/views.py`
- Changing the driver email resets `User.is_verified` to force re-verification review
- The dashboard now surfaces license expiry alerts within 90 days
- Admin profile listings expose state, union, email, and license-alert context

## Migration Strategy

Migration file:

- `drivers/migrations/0002_driverprofile_safety_upgrade.py`

Backward compatibility approach:

- new fields are added as nullable/blank first
- existing profiles are backfilled with account email and phone where available
- existing legacy license values are preserved and re-saved through the encrypted field

## Testing Coverage

Automated coverage includes:

- successful end-to-end driver registration submission
- profile update and re-submission behavior
- underage rejection
- invalid state/LGA rejection
- encrypted-at-rest assertions for sensitive fields
- model-level experience validation
- dashboard expiry alert rendering
- admin approval compatibility

Run locally:

```bash
python manage.py migrate
python manage.py check
python manage.py test drivers dashboard
```

## Data Retention Notes

- Identity, contact, and license records are stored for verification and operational safety review
- Encrypted PII should only be accessed by trusted application flows and authorized operations staff
- If future deletion or export workflows are added, they should operate through the application layer so encrypted fields are handled safely

## API And UI Impact

Updated UI surfaces:

- `templates/drivers/driver_register.html`
- `templates/drivers/driver_profile.html`
- `dashboard/templates/dashboard/dashboard_home.html`

Updated write path:

- `drivers/views.py` `DriverRegistrationView`

No separate JSON API endpoints were present in this app before the upgrade; the primary changes are model, form, template, admin, and dashboard workflow updates.
