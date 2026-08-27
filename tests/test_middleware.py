from django.test import Client, SimpleTestCase
from django.urls import reverse


class CorrelationMiddlewareTests(SimpleTestCase):
    def test_csrf_rejection_still_receives_private_request_id_and_wardveil_headers(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("login"), {"username": "nobody", "password": "irrelevant"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(response["X-Request-ID"]), 32)
        self.assertIn("default-src 'self'", response["Content-Security-Policy"])
        self.assertEqual(response["Cache-Control"], "no-store, max-age=0, private")
