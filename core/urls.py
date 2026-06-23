from django.urls import path

from .views import home, static_test

urlpatterns = [
    path("", home, name="home"),
    path("static-test/", static_test, name="static_test"),
]


