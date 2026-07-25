import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TripShare, LocationUpdate


class LocationTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trip_share_id = self.scope['url_route']['kwargs']['trip_share_id']
        self.trip_share_group = f'trip_share_{self.trip_share_id}'
        query_params = parse_qs(self.scope.get("query_string", b"").decode())
        self.viewer_secret = query_params.get("secret", [""])[0]
        self.broadcaster_token = query_params.get("broadcaster", [""])[0]

        user = self.scope['user']
        self.trip_share = await database_sync_to_async(self.get_trip_share)(self.trip_share_id)
        if not self.trip_share or self.trip_share.status != TripShare.Status.ACTIVE:
            await self.close()
            return

        permissions = await database_sync_to_async(self.resolve_permissions)(user)
        self.can_view = permissions["can_view"]
        self.can_broadcast = permissions["can_broadcast"]
        if not self.can_view:
            await self.close()
            return

        await self.channel_layer.group_add(self.trip_share_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'trip_share_group'):
            await self.channel_layer.group_discard(self.trip_share_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'location_update':
            await self.handle_location_update(data)

    async def handle_location_update(self, data):
        if not self.can_broadcast:
            return
        location = await database_sync_to_async(LocationUpdate.objects.create)(
            trip_share=self.trip_share,
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            accuracy=data.get('accuracy'),
            speed=data.get('speed'),
            heading=data.get('heading'),
            encrypted_data=data.get('encrypted_data'),
            is_gps_signal_lost=data.get('is_gps_signal_lost', False)
        )
        await self.channel_layer.group_send(
            self.trip_share_group,
            {
                'type': 'location_message',
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'accuracy': data.get('accuracy'),
                'speed': data.get('speed'),
                'heading': data.get('heading'),
                'encrypted_data': data.get('encrypted_data'),
                'is_gps_signal_lost': data.get('is_gps_signal_lost', False),
                'timestamp': location.timestamp.isoformat()
            }
        )

    async def location_message(self, event):
        await self.send(text_data=json.dumps(event))

    def get_trip_share(self, share_id):
        try:
            return TripShare.objects.get(id=share_id)
        except TripShare.DoesNotExist:
            return None

    def resolve_permissions(self, user):
        is_authenticated_sharer = user.is_authenticated and user.id == self.trip_share.sharer.id
        is_authenticated_receiver = user.is_authenticated and self.trip_share.receiver and user.id == self.trip_share.receiver.id
        is_secret_viewer = self.viewer_secret == str(self.trip_share.share_secret)
        is_broadcaster = self.broadcaster_token == str(self.trip_share.broadcaster_token)
        return {
            "can_view": bool(is_authenticated_sharer or is_authenticated_receiver or is_secret_viewer or is_broadcaster),
            "can_broadcast": bool(is_authenticated_sharer or is_broadcaster),
        }
