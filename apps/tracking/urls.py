from django.urls import path
from . import views

app_name = "tracking"

urlpatterns = [
    path('share/<uuid:trip_id>/create/', views.TripShareCreateView.as_view(), name='create'),
    path('view/<uuid:share_id>/', views.TripShareView.as_view(), name='view'),
    path('list/', views.TripShareListView.as_view(), name='list'),
]
