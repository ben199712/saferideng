from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from core.notifications import notify_admin_pending_approval, notify_user_action_processed

from django.views.generic import TemplateView


from .constants import STATE_LGA_JSON, STATE_LGA_MAPPING
from .documents import DOCUMENT_REQUIREMENTS, run_malware_scan, store_backup_copy, validate_uploaded_document
from .forms import DriverDocumentUploadForm, DriverRegistrationForm
from .models import DriverDocument, DriverProfile
from apps.vehicles.models import Vehicle, VehicleQRCode


class DriverDocumentMixin:
    document_type_order = (
        "passport_photograph",
        "driver_license",
        "nin_slip",
        "proof_of_address",
        "vehicle_registration",
        "union_membership_card",
    )

    def get_document_map(self, user):
        documents = {
            document.document_type: document
            for document in DriverDocument.objects.filter(user=user).order_by("document_type")
        }
        items = []
        for key in self.document_type_order:
            rule = DOCUMENT_REQUIREMENTS[key]
            document = documents.get(key)
            items.append(
                {
                    "key": key,
                    "label": rule["label"],
                    "required": rule["required"],
                    "document": document,
                }
            )
        return items

    def render_document_form(self):
        return DriverDocumentUploadForm()

    def get_missing_required_documents(self, user):
        uploaded_types = set(DriverDocument.objects.filter(user=user).values_list("document_type", flat=True))
        return [
            rule["label"]
            for key, rule in DOCUMENT_REQUIREMENTS.items()
            if rule["required"] and key not in uploaded_types
        ]

    def get_document_context(self, request):
        return {
            "document_items": self.get_document_map(request.user),
            "document_upload_form": self.render_document_form(),
        }


class DriverProfileView(LoginRequiredMixin, DriverDocumentMixin, TemplateView):
    template_name = "drivers/driver_profile.html"

    def get(self, request, *args, **kwargs):
        profile = DriverProfile.objects.filter(user=request.user).first()
        legacy_vehicle_label = ""
        if profile:
            legacy_vehicle_label = f"{profile.vehicle_make or ''} {profile.vehicle_model or ''}".strip() or "Not submitted"
        return render(
            request,
            self.template_name,
            {
                "profile": profile,
                "profile_exists": profile is not None,
                "legacy_vehicle_label": legacy_vehicle_label,
                "state_lga_mapping": STATE_LGA_MAPPING,
                "state_lga_json": STATE_LGA_JSON,
                **self.get_document_context(request),
            },
        )


class DriverRegistrationView(LoginRequiredMixin, DriverDocumentMixin, View):
    template_name = "drivers/driver_register.html"

    def get_profile(self, request):
        return DriverProfile.objects.filter(user=request.user).first()

    def get(self, request, *args, **kwargs):
        profile = self.get_profile(request)
        form = DriverRegistrationForm(instance=profile, user=request.user)
        context = {"form": form, "profile": profile, "state_lga_mapping": STATE_LGA_MAPPING, "state_lga_json": STATE_LGA_JSON}
        context.update(self.get_document_context(request))
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        profile = self.get_profile(request)
        form = DriverRegistrationForm(request.POST, instance=profile, user=request.user)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        context_factory = {
            "form": form,
            "profile": profile,
            "state_lga_mapping": STATE_LGA_MAPPING,
            "state_lga_json": STATE_LGA_JSON,
        }
        if not form.is_valid():
            if is_ajax:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "Please fix the highlighted fields and try again.",
                        "errors": form.errors.get_json_data(),
                    },
                    status=400,
                )
            context = {**context_factory}
            context.update(self.get_document_context(request))
            return render(request, self.template_name, context)

        missing_documents = self.get_missing_required_documents(request.user)
        if missing_documents:
            form.add_error(None, f"Upload the required documents before submitting: {', '.join(missing_documents)}.")
            if is_ajax:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": f"Upload the required documents before submitting: {', '.join(missing_documents)}.",
                        "errors": form.errors.get_json_data(),
                    },
                    status=400,
                )
            context = {**context_factory}
            context.update(self.get_document_context(request))
            return render(request, self.template_name, context)

        created = profile is None
        profile = form.save(commit=False)
        if profile.user_id is None:
            profile.user = request.user
        profile.verification_status = DriverProfile.VerificationStatus.pending
        profile.is_approved = False
        profile.save()

        user = request.user
        email_changed = user.email != profile.email
        user.email = profile.email
        user.phone_number = profile.phone_number or ""
        if email_changed:
            user.is_verified = False
        user.save(update_fields=["email", "phone_number", "is_verified", "updated_at"])

        profile_url = request.build_absolute_uri(reverse("driver_profile"))
        redirect_url = reverse("driver_profile")
        if created:
            success_message = "Driver profile submitted. Awaiting verification."
            messages.success(request, success_message)
            notify_user_action_processed(
                user=user,
                action_title="Driver profile submitted",
                action_summary="Your driver profile has been received and is now awaiting verification.",
                details=[
                    "Verification status: Pending",
                    f"Profile page: {profile_url}",
                ],
                request=request,
            )
            notify_admin_pending_approval(
                actor_user=user,
                pending_title="Driver profile pending approval",
                pending_summary="A driver submitted a profile that requires admin verification.",
                details=[
                    f"Driver: {user.full_name} ({user.email})",
                    f"State: {profile.state or '-'}",
                    f"LGA: {profile.lga or '-'}",
                    f"License expiry: {profile.driver_license_expiry_date or '-'}",
                ],
                request=request,
            )
        else:
            success_message = "Driver profile updated and resubmitted for verification."
            messages.success(request, success_message)
            notify_user_action_processed(
                user=user,
                action_title="Driver profile updated",
                action_summary="Your updated driver profile has been resubmitted and is now awaiting verification.",
                details=[
                    "Verification status: Pending",
                    f"Profile page: {profile_url}",
                ],
                request=request,
            )
            notify_admin_pending_approval(
                actor_user=user,
                pending_title="Driver profile update pending approval",
                pending_summary="A driver updated their profile and it requires admin verification.",
                details=[
                    f"Driver: {user.full_name} ({user.email})",
                    f"State: {profile.state or '-'}",
                    f"LGA: {profile.lga or '-'}",
                    f"License expiry: {profile.driver_license_expiry_date or '-'}",
                ],
                request=request,
            )
        if is_ajax:
            return JsonResponse(
                {
                    "ok": True,
                    "created": created,
                    "message": success_message,
                    "redirect": redirect_url,
                },
                status=200,
            )
        return redirect("driver_profile")


class DriverDocumentUploadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = DriverDocumentUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            errors = form.errors.get_json_data()
            first_message = "Upload failed."
            for field_errors in errors.values():
                if field_errors:
                    first_message = field_errors[0].get("message", first_message)
                    break
            return JsonResponse({"ok": False, "error": first_message, "errors": errors}, status=400)

        document_type = form.cleaned_data["document_type"]
        uploaded_file = form.cleaned_data["file"]

        try:
            file_metadata = validate_uploaded_document(document_type, uploaded_file)
            scan_status, scan_message = run_malware_scan(uploaded_file)
        except ValidationError as exc:
            message = exc.messages[0] if exc.messages else "Upload failed."
            return JsonResponse({"ok": False, "error": message}, status=400)

        existing = DriverDocument.objects.filter(user=request.user, document_type=document_type).first()
        old_file_name = existing.file.name if existing and existing.file else ""
        old_backup_name = existing.backup_file_name if existing else ""

        document = existing or DriverDocument(user=request.user, document_type=document_type)
        document.file = uploaded_file
        document.original_file_name = uploaded_file.name
        document.file_size = file_metadata["size"]
        document.mime_type = file_metadata["mime_type"]
        document.checksum_sha256 = file_metadata["checksum"]
        document.preview_kind = file_metadata["preview_kind"]
        document.malware_scan_status = scan_status
        document.malware_scan_message = scan_message
        document.save()
        document.backup_file_name = store_backup_copy(document)
        document.save(update_fields=["backup_file_name", "updated_at"])

        if existing and old_file_name and old_file_name != document.file.name and document.file.storage.exists(old_file_name):
            document.file.storage.delete(old_file_name)
        if existing and old_backup_name and old_backup_name != document.backup_file_name:
            from .documents import delete_backup_copy

            delete_backup_copy(old_backup_name)

        return JsonResponse(
            {
                "ok": True,
                "document_type": document.document_type,
                "label": document.document_label,
                "preview_kind": document.preview_kind,
                "preview_url": request.build_absolute_uri(document.get_file_url()),
                "uploaded_at": document.uploaded_at.isoformat(),
                "file_name": document.original_file_name,
                "file_size": document.formatted_size,
                "message": f"{document.document_label} uploaded successfully.",
            }
        )


class DriverDocumentFileView(LoginRequiredMixin, View):
    def get_document(self, request, pk):
        document = get_object_or_404(DriverDocument, pk=pk)
        if request.user.id != document.user_id and not (request.user.is_superuser or request.user.role in ("admin", "super_admin")):
            raise Http404
        return document

    def get(self, request, pk, *args, **kwargs):
        document = self.get_document(request, pk)
        response = FileResponse(document.file.open("rb"), content_type=document.mime_type or "application/octet-stream")
        response["Content-Disposition"] = f'inline; filename="{document.original_file_name}"'
        return response


class DriverDocumentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        document = get_object_or_404(DriverDocument, pk=pk, user=request.user)
        label = document.document_label
        document.delete()
        messages.success(request, f"{label} removed successfully.")
        return redirect("driver_register")


class DriverPublicProfileView(View):
    template_name = "drivers/public_driver_profile.html"

    def get_state(self, vehicle):
        if vehicle.verification_status == Vehicle.VerificationStatus.rejected:
            return "rejected"
        if not vehicle.is_active:
            return "suspended"
        if vehicle.verification_status == Vehicle.VerificationStatus.approved:
            return "verified"
        return "pending"

    def get(self, request, driver_uuid, vehicle_uuid):
        vehicle = get_object_or_404(
            Vehicle.objects.select_related("driver", "qr_code"),
            driver__uuid=driver_uuid,
            uuid=vehicle_uuid,
        )
        qr_code = getattr(vehicle, "qr_code", None)
        state = self.get_state(vehicle)
        scan_count = qr_code.scan_logs.count() if qr_code else 0
        return render(
            request,
            self.template_name,
            {
                "vehicle": vehicle,
                "qr_code": qr_code,
                "state": state,
                "can_start_trip": state == "verified" and bool(qr_code and qr_code.is_active),
                "scan_count": scan_count,
            },
        )
