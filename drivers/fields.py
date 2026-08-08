from django.db import models

from .crypto import decrypt_value, encrypt_value


class EncryptedCharField(models.CharField):
    description = "AES-256 encrypted char field"

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return None if self.null else ""
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def to_python(self, value):
        value = super().to_python(value)
        return decrypt_value(value)


class EncryptedTextField(models.TextField):
    description = "AES-256 encrypted text field"

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return None if self.null else ""
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def to_python(self, value):
        value = super().to_python(value)
        return decrypt_value(value)
