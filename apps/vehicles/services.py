import io
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse as django_reverse
from PIL import Image as PILImage
import qrcode
from qrcode.image.pil import PilImage

from .models import VehicleQRCode


def create_unique_token():
    while True:
        token = uuid.uuid4()
        if not VehicleQRCode.objects.filter(token=token).exists():
            return token


def verification_url(token):
    return django_reverse("verify_vehicle", kwargs={"token": str(token)})


def build_qr_image(target_url, token=None):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    image = qr.make_image(image_factory=PilImage).convert("RGB")
    image = image.resize((512, 512), PILImage.Resampling.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return SimpleUploadedFile(
        f"vehicle-{token or uuid.uuid4()}.png",
        buffer.read(),
        content_type="image/png",
    )


def generate_qr_code(vehicle, target_url=None):
    token = create_unique_token()
    if target_url is None:
        target_url = verification_url(token)
    qr_code, _ = VehicleQRCode.objects.update_or_create(
        vehicle=vehicle,
        defaults={
            "token": token,
            "qr_image": build_qr_image(target_url),
            "is_active": True,
        },
    )
    return qr_code


def get_or_create_qr_code(vehicle):
    qr_code, _ = VehicleQRCode.objects.get_or_create(
        vehicle=vehicle,
        defaults={"token": create_unique_token()},
    )

    if not qr_code.is_active:
        qr_code.token = create_unique_token()
        qr_code.is_active = True
        qr_code.qr_image = build_qr_image(verification_url(qr_code.token), qr_code.token)
        qr_code.save(update_fields=["token", "qr_image", "is_active"])

    return qr_code
