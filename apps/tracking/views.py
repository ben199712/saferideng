from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic import View, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.db import models
from django.contrib.auth import get_user_model
from .models import TripShare, LocationUpdate
from apps.trips.models import Trip
from .utils import generate_rsa_key_pair

User = get_user_model()


class TripShareCreateView(LoginRequiredMixin, View):
    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        if request.user.id != trip.driver_id:
            return HttpResponseForbidden("Not authorized to share this trip.")
        receiver_email = request.POST.get('receiver_email')
        receiver = None
        if receiver_email:
            try:
                receiver = User.objects.get(email=receiver_email)
            except User.DoesNotExist:
                pass
        sharer_private, sharer_public = generate_rsa_key_pair()
        receiver_private = None
        receiver_public = None
        if receiver:
            receiver_private, receiver_public = generate_rsa_key_pair()
        share = TripShare.objects.create(
            trip=trip,
            sharer=request.user,
            receiver=receiver,
            sharer_public_key=sharer_public,
            receiver_public_key=receiver_public,
        )
        request.session[f'sharer_key_{share.id}'] = sharer_private
        if receiver_private:
            request.session[f'receiver_key_{share.id}'] = receiver_private
        return JsonResponse({
            'trip_share_id': str(share.id),
            'share_secret': str(share.share_secret),
            'sharer_private_key': sharer_private,
            'receiver_private_key': receiver_private,
            'share_url': request.build_absolute_uri(reverse('tracking:view', kwargs={'share_id': share.id})),
        })


class TripShareView(LoginRequiredMixin, DetailView):
    model = TripShare
    template_name = "tracking/live_tracking.html"
    pk_url_kwarg = "share_id"
    context_object_name = "trip_share"

    def get_object(self, queryset=None):
        share = super().get_object(queryset)
        user = self.request.user
        is_sharer = user.id == share.sharer.id
        is_receiver = share.receiver and user.id == share.receiver.id
        if not is_sharer and not is_receiver:
            secret = self.request.GET.get('secret')
            if not secret or str(share.share_secret) != secret:
                raise PermissionDenied("Not authorized")
        return share

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        share = self.get_object()
        user = self.request.user
        locations = list(
            LocationUpdate.objects.filter(trip_share=share)
            .order_by("timestamp")
            .values("latitude", "longitude", "accuracy", "speed", "heading", "timestamp", "is_gps_signal_lost")
        )
        ctx['is_sharer'] = (user.id == share.sharer.id)
        ctx['is_receiver'] = (share.receiver and user.id == share.receiver.id) or ('secret' in self.request.GET)
        ctx['last_location'] = LocationUpdate.objects.filter(trip_share=share).order_by('-timestamp').first()
        if ctx['is_sharer']:
            ctx['private_key'] = self.request.session.get(f'sharer_key_{share.id}', '')
        if ctx['is_receiver']:
            ctx['private_key'] = self.request.session.get(f'receiver_key_{share.id}', '')
        ctx['receiver_public_key'] = share.receiver_public_key or share.sharer_public_key
        ctx['history_points'] = [
            {
                "latitude": float(point["latitude"]),
                "longitude": float(point["longitude"]),
                "accuracy": point["accuracy"],
                "speed": point["speed"],
                "heading": point["heading"],
                "timestamp": point["timestamp"].isoformat(),
                "is_gps_signal_lost": point["is_gps_signal_lost"],
            }
            for point in locations
        ]
        ctx['geofence_radius_meters'] = 250
        return ctx


class TripShareListView(LoginRequiredMixin, ListView):
    template_name = "tracking/share_list.html"
    context_object_name = "shares"

    def get_queryset(self):
        user = self.request.user
        return TripShare.objects.filter(
            models.Q(sharer=user) | models.Q(receiver=user)
        ).order_by('-created_at').select_related('trip', 'sharer', 'receiver')
