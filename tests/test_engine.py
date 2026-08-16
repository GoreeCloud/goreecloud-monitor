from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from monitoring.engine import CheckOutcome, _apply_outcome, check_push
from monitoring.models import Incident, Monitor


class EngineStateTests(TestCase):
    def setUp(self):
        self.monitor = Monitor.objects.create(
            name="service",
            kind=Monitor.Kind.PUSH,
            interval_seconds=60,
            heartbeat_grace_seconds=30,
            failure_threshold=2,
            recovery_threshold=1,
        )

    def test_failure_threshold_opens_one_incident(self):
        now = timezone.now()
        _apply_outcome(self.monitor.id, CheckOutcome(False, Monitor.State.DOWN, None, "failure 1"), now)
        self.monitor.refresh_from_db()
        self.assertNotEqual(self.monitor.state, Monitor.State.DOWN)
        _apply_outcome(self.monitor.id, CheckOutcome(False, Monitor.State.DOWN, None, "failure 2"), now + timedelta(seconds=1))
        self.monitor.refresh_from_db()
        self.assertEqual(self.monitor.state, Monitor.State.DOWN)
        self.assertEqual(Incident.objects.filter(monitor=self.monitor, ended_at__isnull=True).count(), 1)

    def test_recovery_closes_incident(self):
        now = timezone.now()
        self.monitor.failure_threshold = 1
        self.monitor.save()
        _apply_outcome(self.monitor.id, CheckOutcome(False, Monitor.State.DOWN, None, "down"), now)
        _apply_outcome(self.monitor.id, CheckOutcome(True, Monitor.State.UP, None, "up"), now + timedelta(seconds=1))
        self.monitor.refresh_from_db()
        self.assertEqual(self.monitor.state, Monitor.State.UP)
        self.assertFalse(Incident.objects.filter(monitor=self.monitor, ended_at__isnull=True).exists())

    async def test_push_monitor_detects_stale_heartbeat(self):
        self.monitor.last_heartbeat_at = timezone.now() - timedelta(seconds=100)
        outcome = await check_push(self.monitor)
        self.assertFalse(outcome.success)

    async def test_push_monitor_accepts_current_heartbeat(self):
        self.monitor.last_heartbeat_at = timezone.now()
        outcome = await check_push(self.monitor)
        self.assertTrue(outcome.success)
