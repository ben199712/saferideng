# RideGuarde Live Tracking

## Overview

The tracking module provides real-time trip sharing with Leaflet.js map rendering, Django Channels WebSocket delivery, route playback, and a geofence overlay around the latest live position.

## Frontend Templates

- `templates/tracking/live_tracking.html`
  - Renders the live map UI
  - Connects to the WebSocket feed at `/ws/tracking/<trip_share_id>/`
  - Shows live marker updates, route trail, historical playback, and the geofence circle
- `templates/tracking/share_list.html`
  - Lists all trip shares visible to the authenticated user
  - Links directly to the live tracking screen

## Backend Integration Points

- `apps/tracking/views.py`
  - `TripShareCreateView`
    - Creates a new share and optionally attaches a receiver
    - Returns JSON including the share URL and generated keys
  - `TripShareView`
    - Renders the live tracking template
    - Injects historical route data and geofence configuration into the template
  - `TripShareListView`
    - Lists shares for the current user
- `apps/tracking/consumers.py`
  - `LocationTrackingConsumer`
    - Authenticates the WebSocket connection
    - Persists incoming coordinates
    - Broadcasts updates to all authorized viewers

## WebSocket Payload

Incoming and outgoing location updates use this shape:

```json
{
  "type": "location_update",
  "latitude": 9.123456,
  "longitude": 7.654321,
  "accuracy": 8.0,
  "speed": 5.5,
  "heading": 180.0,
  "encrypted_data": null,
  "is_gps_signal_lost": false
}
```

## Configuration

- `requirements.txt`
  - `channels`
  - `channels-redis`
  - `daphne`
  - `redis`
  - `pycryptodome`
- `saferide/settings.py`
  - `ASGI_APPLICATION = "saferide.asgi.application"`
  - `CHANNEL_LAYERS` uses `channels_redis.core.RedisChannelLayer`
  - Set `REDIS_URL` in production
- `Procfile`
  - Uses Daphne so HTTP and WebSocket traffic are both supported

## Leaflet Features Included

- Custom live and playback markers
- Real-time marker movement from WebSocket messages
- Zoom and pan controls from Leaflet defaults
- Popups with location details
- Timestamp display for the latest update
- Geofence circle overlay
- Historical route playback with slider and autoplay
- Canvas-backed polyline rendering for better update performance

## Performance Notes

- The map uses `preferCanvas: true` to reduce redraw overhead during frequent updates.
- The playback route and live route are drawn separately so replay does not disrupt the live polyline.
- The client queues outbound updates while disconnected and flushes them after reconnect.

## Troubleshooting

- WebSocket does not connect
  - Confirm `daphne` is the active process in `Procfile`
  - Confirm the `REDIS_URL` environment variable is set in production
  - Confirm `channels-redis` is installed
- Map tiles do not load
  - Check network access to `https://{s}.tile.openstreetmap.org`
  - Ensure the browser is not blocking third-party requests
- Live updates do not appear
  - Confirm the viewer is either the share receiver or the share owner
  - Confirm the browser granted geolocation permission
  - Confirm the share status is still `active`
- GPS shows signal lost
  - The browser could not return a fresh high-accuracy fix
  - The UI keeps the last known point visible until a new update arrives

## Testing

Run the tracking tests with:

```bash
python manage.py test apps.tracking
```

The tests cover:

- encryption round-trip
- share creation permissions
- live tracking page rendering
- authorization rules
- responsive template hooks
