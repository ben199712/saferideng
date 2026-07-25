import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TripShare, LocationUpdate


class LocationTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trip_share_id = self.scope['url_route']['kwargs']['trip_share_id']
        self.trip_share_group = f'trip_share_{self.trip_share_id}'

        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return

        self.trip_share = await database_sync_to_async(self.get_trip_share)(self.trip_share_id)
        if not self.trip_share or self.trip_share.status != TripShare.Status.ACTIVE:
            await self.close()
            return

        if not await database_sync_to_async(self.is_authorized)(user):
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
        if self.scope['user'].id != self.trip_share.sharer.id:
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

    def is_authorized(self, user):
        return user.id == self.trip_share.sharer.id or (self.trip_share.receiver and user.id == self.trip_share.receiver.id)
