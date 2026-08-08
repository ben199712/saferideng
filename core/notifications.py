from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from accounts.models import User

from .models import EmailNotificationLog
from .resend import ResendError, send_resend_email


def get_admin_notification_emails():
    configured = getattr(settings, "ADMIN_NOTIFICATION_EMAILS", []) or []
    if configured:
        return configured

    admins = User.objects.filter(
        role__in=[User.Roles.admin, User.Roles.super_admin]
    ).exclude(email="")

    superusers = User.objects.filter(
        is_superuser=True
    ).exclude(email="")

    emails = list(
        (admins | superusers)
        .values_list("email", flat=True)
        .distinct()
    )

    return emails


def render_email(template_base, context):
    html = render_to_string(
        f"emails/{template_base}.html",
        context,
    )

    text = render_to_string(
        f"emails/{template_base}.txt",
        context,
    )

    return html, text


def send_logged_email(
    *,
    event_type,
    to_email,
    subject,
    template_base,
    context,
    actor_user=None,
    target_user=None,
    request=None,
):
    request_path = getattr(request, "path", "") if request else ""

    ip_address = ""
    if request:
        ip_address = request.META.get("REMOTE_ADDR") or ""

    log = EmailNotificationLog.objects.create(
        event_type=event_type,
        actor_user=actor_user,
        target_user=target_user,
        to_email=to_email,
        subject=subject,
        status=EmailNotificationLog.Status.pending,
        provider="resend",
        request_path=request_path,
        ip_address=ip_address or None,
        payload=context or {},
    )

    html, text = render_email(template_base, context)

    api_key = (getattr(settings, "RESEND_API_KEY", "") or "").strip()

    # ----------------------------------------------------
    # No Resend API key -> use Django email backend
    # ----------------------------------------------------
    if not api_key:
        email_backend = getattr(settings, "EMAIL_BACKEND", "") or ""

        provider_label = "django"

        if "locmem" in email_backend:
            provider_label = "locmem"
        elif "console" in email_backend:
            provider_label = "console"

        log.provider = provider_label

        try:
            from_email = (
                getattr(settings, "DEFAULT_FROM_EMAIL", "")
                or getattr(settings, "RESEND_FROM_EMAIL", "")
            )

            message = EmailMessage(
                subject=subject,
                body=text or html,
                from_email=from_email,
                to=[to_email],
            )

            if html:
                message.content_subtype = "html"

            message.send()

            log.status = EmailNotificationLog.Status.sent
            log.provider_message_id = ""
            log.error_message = ""

            log.save(
                update_fields=[
                    "provider",
                    "status",
                    "provider_message_id",
                    "error_message",
                ]
            )

            return log

        except Exception as exc:
            log.status = EmailNotificationLog.Status.failed
            log.error_message = str(exc)

            log.save(
                update_fields=[
                    "provider",
                    "status",
                    "error_message",
                ]
            )

            return log

    # ----------------------------------------------------
    # Send using Resend
    # ----------------------------------------------------
    try:
        message_id, response_body = send_resend_email(
            api_key=api_key,
            from_email=getattr(
                settings,
                "RESEND_FROM_EMAIL",
                getattr(settings, "DEFAULT_FROM_EMAIL", ""),
            ),
            to_email=to_email,
            subject=subject,
            html=html,
            text=text,
        )

        log.provider = "resend"
        log.status = EmailNotificationLog.Status.sent
        log.provider_message_id = message_id
        log.error_message = response_body or ""

        log.save(
            update_fields=[
                "provider",
                "status",
                "provider_message_id",
                "error_message",
            ]
        )

        return log

    except ResendError as exc:
        log.provider = "resend"
        log.status = EmailNotificationLog.Status.failed
        log.error_message = (
            f"{exc} {getattr(exc, 'response_body', '')}"
        ).strip()

        log.save(
            update_fields=[
                "provider",
                "status",
                "error_message",
            ]
        )

        return log

    except Exception as exc:
        log.provider = "resend"
        log.status = EmailNotificationLog.Status.failed
        log.error_message = str(exc)

        log.save(
            update_fields=[
                "provider",
                "status",
                "error_message",
            ]
        )

        return log


def notify_user_action_processed(
    *,
    user,
    action_title,
    action_summary,
    details=None,
    request=None,
):
    if not user or not user.email:
        return None

    context = {
        "title": action_title,
        "summary": action_summary,
        "details": details or [],
    }

    return send_logged_email(
        event_type="user_action_processed",
        to_email=user.email,
        subject=f"Action confirmed: {action_title}",
        template_base="user_action_processed",
        context=context,
        actor_user=user,
        target_user=user,
        request=request,
    )


def notify_admin_pending_approval(
    *,
    actor_user,
    pending_title,
    pending_summary,
    details=None,
    request=None,
):
    recipients = get_admin_notification_emails()

    context = {
        "title": pending_title,
        "summary": pending_summary,
        "details": details or [],
        "actor_email": getattr(actor_user, "email", ""),
        "actor_name": getattr(actor_user, "full_name", ""),
    }

    logs = []

    for email in recipients:
        logs.append(
            send_logged_email(
                event_type="admin_pending_approval",
                to_email=email,
                subject=f"Approval required: {pending_title}",
                template_base="admin_pending_approval",
                context=context,
                actor_user=actor_user,
                target_user=None,
                request=request,
            )
        )

    return logs


def notify_user_admin_action(
    *,
    admin_user,
    target_user,
    action_title,
    action_summary,
    details=None,
    request=None,
):
    if not target_user or not target_user.email:
        return None

    context = {
        "title": action_title,
        "summary": action_summary,
        "details": details or [],
        "admin_email": getattr(admin_user, "email", ""),
        "admin_name": getattr(admin_user, "full_name", ""),
    }

    return send_logged_email(
        event_type="admin_action_on_user",
        to_email=target_user.email,
        subject=f"Update: {action_title}",
        template_base="user_admin_update",
        context=context,
        actor_user=admin_user,
        target_user=target_user,
        request=request,
    )