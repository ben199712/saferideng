import json
import urllib.request
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from apps.tracking.models import TripShare
from drivers.models import DriverProfile

from .models import EmergencyAlert, SOSAlertDeliveryLog, SOSAuthorityContact


def get_or_create_public_share(trip):
    share, _ = TripShare.objects.get_or_create(
        trip=trip,
        receiver=None,
        status=TripShare.Status.ACTIVE,
        defaults={
            "sharer": trip.driver,
        },
    )
    return share


def build_tracking_share_url(request, trip):
    share = get_or_create_public_share(trip)
    base_url = reverse("tracking:view", kwargs={"share_id": str(share.id)})
    query = urlencode({"secret": str(share.share_secret)})
    return request.build_absolute_uri(f"{base_url}?{query}")


def get_latest_location_for_trip(trip):
    share = get_or_create_public_share(trip)
    location = share.locations.order_by("-timestamp").first()
    if not location:
        return None
    age_seconds = int((timezone.now() - location.timestamp).total_seconds()) if location.timestamp else None
    return {
        "latitude": float(location.latitude),
        "longitude": float(location.longitude),
        "timestamp": location.timestamp.isoformat(),
        "age_seconds": age_seconds,
    }


def build_sos_snapshot(request, alert):
    trip = alert.trip
    vehicle = trip.vehicle
    driver = trip.driver
    driver_profile = DriverProfile.objects.filter(user=driver).first()
    latest_location = get_latest_location_for_trip(trip)

    snapshot = {
        "alert": {
            "uuid": str(alert.uuid),
            "type": alert.alert_type,
            "status": alert.status,
            "created_at": alert.created_at.isoformat() if alert.created_at else timezone.now().isoformat(),
            "message": alert.message,
        },
        "location": latest_location or {},
        "trip": {
            "uuid": str(trip.uuid),
            "origin": trip.start_location,
            "destination": trip.destination,
            "route": vehicle.registered_route,
            "status": trip.trip_status,
            "started_at": trip.started_at.isoformat() if trip.started_at else "",
            "current_progress": "Live tracking link included for real-time progress.",
            "tracking_url": request.build_absolute_uri(reverse("trip_detail", kwargs={"uuid": str(trip.uuid)})),
            "live_tracking_url": build_tracking_share_url(request, trip),
        },
        "driver": {
            "id": driver.id,
            "full_name": driver.full_name,
            "email": (driver_profile.email if driver_profile and driver_profile.email else driver.email),
            "phone_number": (driver_profile.phone_number if driver_profile and driver_profile.phone_number else driver.phone_number),
            "license_number": (driver_profile.license_number if driver_profile and driver_profile.license_number else ""),
        },
        "vehicle": {
            "plate_number": vehicle.plate_number,
            "make": vehicle.vehicle_make,
            "model": vehicle.vehicle_model,
            "color": vehicle.vehicle_color,
            "insurance_number": vehicle.insurance_number,
            "insurance_status": "Provided" if vehicle.insurance_number else "Missing",
            "verification_status": vehicle.verification_status,
        },
        "passenger": {
            "name": trip.passenger_name,
            "phone_number": trip.passenger_phone,
        },
    }
    return snapshot


def build_email_body(snapshot):
    loc = snapshot.get("location") or {}
    trip = snapshot.get("trip") or {}
    driver = snapshot.get("driver") or {}
    vehicle = snapshot.get("vehicle") or {}
    passenger = snapshot.get("passenger") or {}

    lines = [
        "SAFE RIDE SOS ALERT",
        "",
        f"Alert ID: {snapshot.get('alert', {}).get('uuid', '')}",
        f"Alert Type: {snapshot.get('alert', {}).get('type', '')}",
        f"Created: {snapshot.get('alert', {}).get('created_at', '')}",
        "",
        "LOCATION",
        f"Latitude: {loc.get('latitude', '')}",
        f"Longitude: {loc.get('longitude', '')}",
        f"Timestamp: {loc.get('timestamp', '')}",
        "",
        "TRIP",
        f"Origin: {trip.get('origin', '')}",
        f"Destination: {trip.get('destination', '')}",
        f"Route: {trip.get('route', '')}",
        f"Status: {trip.get('status', '')}",
        f"Started: {trip.get('started_at', '')}",
        f"Trip Page: {trip.get('tracking_url', '')}",
        f"Live Tracking: {trip.get('live_tracking_url', '')}",
        "",
        "DRIVER",
        f"Name: {driver.get('full_name', '')}",
        f"License: {driver.get('license_number', '')}",
        f"Phone: {driver.get('phone_number', '')}",
        f"Email: {driver.get('email', '')}",
        "",
        "VEHICLE",
        f"Plate: {vehicle.get('plate_number', '')}",
        f"Make/Model: {vehicle.get('make', '')} {vehicle.get('model', '')}".strip(),
        f"Color: {vehicle.get('color', '')}",
        f"Insurance: {vehicle.get('insurance_number', '')}",
        f"Insurance Status: {vehicle.get('insurance_status', '')}",
        "",
        "PASSENGER",
        f"Name: {passenger.get('name', '')}",
        f"Phone: {passenger.get('phone_number', '')}",
        "",
    ]
    return "\n".join(lines)


def build_sms_body(snapshot):
    loc = snapshot.get("location") or {}
    trip = snapshot.get("trip") or {}
    driver = snapshot.get("driver") or {}
    vehicle = snapshot.get("vehicle") or {}
    coords = ""
    if loc.get("latitude") and loc.get("longitude"):
        coords = f"{loc.get('latitude')},{loc.get('longitude')}"
    return (
        "SAFE RIDE SOS ALERT\n"
        f"Trip: {trip.get('uuid', '')}\n"
        f"Driver: {driver.get('full_name', '')}\n"
        f"Plate: {vehicle.get('plate_number', '')}\n"
        f"From: {trip.get('origin', '')}\n"
        f"To: {trip.get('destination', '')}\n"
        f"Location: {coords}\n"
        f"Track: {trip.get('live_tracking_url', '')}"
    )


def send_email(to_email, subject, body):
    message = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[to_email],
    )
    sent_count = message.send(fail_silently=False)
    return str(sent_count), "sent"


def send_sms_http_json(to_number, body):
    endpoint = getattr(settings, "SOS_SMS_HTTP_ENDPOINT", "")
    token = getattr(settings, "SOS_SMS_HTTP_AUTH_TOKEN", "")
    sender = getattr(settings, "SOS_SMS_HTTP_SENDER_ID", "SafeRide")
    if not endpoint:
        raise ValueError("SMS endpoint is not configured.")

    payload = {"to": to_number, "message": body, "sender_id": sender}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        response_body = resp.read().decode("utf-8", errors="ignore")
        return str(resp.status), response_body[:1000]


def send_sms(to_number, body):
    provider = getattr(settings, "SOS_SMS_PROVIDER", "console")
    if provider == "console":
        return "console", "skipped"
    if provider == "http_json":
        return send_sms_http_json(to_number, body)
    raise ValueError("Unsupported SMS provider.")


def log_delivery(
    *,
    alert,
    recipient_type,
    channel,
    destination,
    status,
    authority_contact=None,
    admin_user=None,
    provider_reference="",
    response_message="",
    delivered_at=None,
):
    return SOSAlertDeliveryLog.objects.create(
        alert=alert,
        authority_contact=authority_contact,
        admin_user=admin_user,
        recipient_type=recipient_type,
        channel=channel,
        destination=destination,
        status=status,
        provider_reference=provider_reference,
        response_message=response_message,
        delivered_at=delivered_at,
    )


def notify_sos(alert, request):
    snapshot = build_sos_snapshot(request, alert)
    alert.details_snapshot = snapshot
    alert.save(update_fields=["details_snapshot"])

    subject = f"SafeRide SOS Alert ({snapshot.get('vehicle', {}).get('plate_number', '')})"
    email_body = build_email_body(snapshot)
    sms_body = build_sms_body(snapshot)

    authority_contacts = SOSAuthorityContact.objects.filter(is_active=True)
    for contact in authority_contacts:
        if contact.official_email:
            try:
                reference, message = send_email(contact.official_email, subject, email_body)
                log_delivery(
                    alert=alert,
                    recipient_type=SOSAlertDeliveryLog.RecipientType.authority,
                    channel=SOSAlertDeliveryLog.Channel.email,
                    destination=contact.official_email,
                    status=SOSAlertDeliveryLog.DeliveryStatus.sent,
                    authority_contact=contact,
                    provider_reference=reference,
                    response_message=message,
                    delivered_at=timezone.now(),
                )
            except Exception as exc:
                log_delivery(
                    alert=alert,
                    recipient_type=SOSAlertDeliveryLog.RecipientType.authority,
                    channel=SOSAlertDeliveryLog.Channel.email,
                    destination=contact.official_email,
                    status=SOSAlertDeliveryLog.DeliveryStatus.failed,
                    authority_contact=contact,
                    response_message=str(exc),
                )

        if contact.sms_phone_number:
            try:
                reference, message = send_sms(contact.sms_phone_number, sms_body)
                status = SOSAlertDeliveryLog.DeliveryStatus.sent
                if reference == "console" and message == "skipped":
                    status = SOSAlertDeliveryLog.DeliveryStatus.skipped
                log_delivery(
                    alert=alert,
                    recipient_type=SOSAlertDeliveryLog.RecipientType.authority,
                    channel=SOSAlertDeliveryLog.Channel.sms,
                    destination=contact.sms_phone_number,
                    status=status,
                    authority_contact=contact,
                    provider_reference=reference,
                    response_message=message,
                    delivered_at=timezone.now() if status == SOSAlertDeliveryLog.DeliveryStatus.sent else None,
                )
            except Exception as exc:
                log_delivery(
                    alert=alert,
                    recipient_type=SOSAlertDeliveryLog.RecipientType.authority,
                    channel=SOSAlertDeliveryLog.Channel.sms,
                    destination=contact.sms_phone_number,
                    status=SOSAlertDeliveryLog.DeliveryStatus.failed,
                    authority_contact=contact,
                    response_message=str(exc),
                )

    admin_users = User.objects.filter(
        models.Q(role__in=[User.Roles.admin, User.Roles.super_admin]) | models.Q(is_superuser=True)
    ).exclude(email="")
    for admin_user in admin_users:
        try:
            reference, message = send_email(admin_user.email, subject, email_body)
            log_delivery(
                alert=alert,
                recipient_type=SOSAlertDeliveryLog.RecipientType.admin,
                channel=SOSAlertDeliveryLog.Channel.email,
                destination=admin_user.email,
                status=SOSAlertDeliveryLog.DeliveryStatus.sent,
                admin_user=admin_user,
                provider_reference=reference,
                response_message=message,
                delivered_at=timezone.now(),
            )
        except Exception as exc:
            log_delivery(
                alert=alert,
                recipient_type=SOSAlertDeliveryLog.RecipientType.admin,
                channel=SOSAlertDeliveryLog.Channel.email,
                destination=admin_user.email,
                status=SOSAlertDeliveryLog.DeliveryStatus.failed,
                admin_user=admin_user,
                response_message=str(exc),
            )

        if admin_user.phone_number:
            try:
                reference, message = send_sms(admin_user.phone_number, sms_body)
                status = SOSAlertDeliveryLog.DeliveryStatus.sent
                if reference == "console" and message == "skipped":
                    status = SOSAlertDeliveryLog.DeliveryStatus.skipped
                log_delivery(
                    alert=alert,
                    recipient_type=SOSAlertDeliveryLog.RecipientType.admin,
                    channel=SOSAlertDeliveryLog.Channel.sms,
                    destination=admin_user.phone_number,
                    status=status,
                    admin_user=admin_user,
                    provider_reference=reference,
                    response_message=message,
                    delivered_at=timezone.now() if status == SOSAlertDeliveryLog.DeliveryStatus.sent else None,
                )
            except Exception as exc:
                log_delivery(
                    alert=alert,
                    recipient_type=SOSAlertDeliveryLog.RecipientType.admin,
                    channel=SOSAlertDeliveryLog.Channel.sms,
                    destination=admin_user.phone_number,
                    status=SOSAlertDeliveryLog.DeliveryStatus.failed,
                    admin_user=admin_user,
                    response_message=str(exc),
                )

    return snapshot
