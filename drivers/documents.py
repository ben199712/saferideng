import hashlib
import mimetypes
import shutil
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible
from django.utils import timezone


@deconstructible
class PrivateDriverDocumentStorage(FileSystemStorage):
    @property
    def base_location(self):
        return str(settings.PRIVATE_DRIVER_DOCUMENTS_ROOT)

    @property
    def location(self):
        return self.base_location


PRIVATE_DRIVER_STORAGE = PrivateDriverDocumentStorage()

MAX_UPLOAD_BYTES = settings.DRIVER_DOCUMENT_MAX_UPLOAD_BYTES

IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
PDF_MIME_TYPES = {"application/pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PDF_EXTENSIONS = {".pdf"}

DOCUMENT_REQUIREMENTS = {
    "passport_photograph": {
        "label": "Passport Photograph",
        "required": True,
        "mime_types": IMAGE_MIME_TYPES,
        "extensions": IMAGE_EXTENSIONS,
        "preview_kind": "image",
    },
    "driver_license": {
        "label": "Driver License",
        "required": True,
        "mime_types": IMAGE_MIME_TYPES | PDF_MIME_TYPES,
        "extensions": IMAGE_EXTENSIONS | PDF_EXTENSIONS,
        "preview_kind": "auto",
    },
    "nin_slip": {
        "label": "NIN Slip",
        "required": True,
        "mime_types": IMAGE_MIME_TYPES | PDF_MIME_TYPES,
        "extensions": IMAGE_EXTENSIONS | PDF_EXTENSIONS,
        "preview_kind": "auto",
    },
    "proof_of_address": {
        "label": "Proof of Address",
        "required": True,
        "mime_types": IMAGE_MIME_TYPES | PDF_MIME_TYPES,
        "extensions": IMAGE_EXTENSIONS | PDF_EXTENSIONS,
        "preview_kind": "auto",
    },
    "vehicle_registration": {
        "label": "Vehicle Registration",
        "required": False,
        "mime_types": IMAGE_MIME_TYPES | PDF_MIME_TYPES,
        "extensions": IMAGE_EXTENSIONS | PDF_EXTENSIONS,
        "preview_kind": "auto",
    },
    "union_membership_card": {
        "label": "Union Membership Card",
        "required": False,
        "mime_types": IMAGE_MIME_TYPES | PDF_MIME_TYPES,
        "extensions": IMAGE_EXTENSIONS | PDF_EXTENSIONS,
        "preview_kind": "auto",
    },
}


def driver_document_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"{instance.user_id}/{instance.document_type}/{uuid.uuid4().hex}{extension}"


def get_document_requirement(document_type):
    return DOCUMENT_REQUIREMENTS[document_type]


def detect_mime_type(uploaded_file):
    provided = getattr(uploaded_file, "content_type", "") or ""
    guessed, _ = mimetypes.guess_type(getattr(uploaded_file, "name", ""))
    return provided or guessed or "application/octet-stream"


def build_file_checksum(uploaded_file):
    uploaded_file.seek(0)
    digest = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        digest.update(chunk)
    uploaded_file.seek(0)
    return digest.hexdigest()


def infer_preview_kind(mime_type):
    if mime_type in IMAGE_MIME_TYPES:
        return "image"
    if mime_type in PDF_MIME_TYPES:
        return "pdf"
    return "generic"


def validate_uploaded_document(document_type, uploaded_file):
    if not uploaded_file:
        raise ValidationError("Choose a file to upload.")

    rule = get_document_requirement(document_type)
    extension = Path(uploaded_file.name).suffix.lower()
    mime_type = detect_mime_type(uploaded_file)

    if uploaded_file.size > MAX_UPLOAD_BYTES:
        raise ValidationError(f"File is too large. Maximum upload size is {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.")

    if extension not in rule["extensions"]:
        raise ValidationError("This file type is not allowed for the selected document.")

    if mime_type not in rule["mime_types"]:
        raise ValidationError("Uploaded file content type is not supported.")

    uploaded_file.seek(0)
    sample = uploaded_file.read(8)
    uploaded_file.seek(0)

    if mime_type in PDF_MIME_TYPES and not sample.startswith(b"%PDF"):
        raise ValidationError("The uploaded PDF file appears to be invalid.")

    return {
        "mime_type": mime_type,
        "preview_kind": infer_preview_kind(mime_type),
        "checksum": build_file_checksum(uploaded_file),
        "size": uploaded_file.size,
    }


def run_malware_scan(uploaded_file):
    if not settings.DRIVER_DOCUMENT_MALWARE_SCAN_ENABLED:
        return "skipped", "Malware scanning disabled"

    try:
        import clamd  # type: ignore
    except ImportError:
        return "skipped", "Malware scanner library not installed"

    uploaded_file.seek(0)
    client = clamd.ClamdNetworkSocket()
    result = client.instream(uploaded_file)
    uploaded_file.seek(0)
    status = (result or {}).get("stream", ("UNKNOWN", "No result"))
    if status[0] == "FOUND":
        raise ValidationError("Upload rejected because malware was detected.")
    if status[0] != "OK":
        return "failed", str(status[1])
    return "clean", "No malware detected"


def store_backup_copy(document):
    if not document.file:
        return ""

    source_path = Path(document.file.path)
    backup_root = Path(settings.PRIVATE_DRIVER_DOCUMENTS_BACKUP_ROOT)
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / document.file.name
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, backup_path)
    return document.file.name


def delete_backup_copy(relative_path):
    if not relative_path:
        return
    backup_path = Path(settings.PRIVATE_DRIVER_DOCUMENTS_BACKUP_ROOT) / relative_path
    if backup_path.exists():
        backup_path.unlink()
        parent = backup_path.parent
        while parent != Path(settings.PRIVATE_DRIVER_DOCUMENTS_BACKUP_ROOT) and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent


def format_file_size(size):
    if size is None:
        return "-"
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def current_timestamp():
    return timezone.now()
