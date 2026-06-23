from django.contrib.staticfiles.finders import find
from django.test import Client, TestCase
from django.urls import reverse


class PublicPageTests(TestCase):
    def test_home_and_static_test_pages_render(self):
        client = Client()

        self.assertEqual(client.get(reverse("home")).status_code, 200)
        self.assertEqual(client.get(reverse("static_test")).status_code, 200)
        self.assertIsNotNone(find("logo.svg"))
