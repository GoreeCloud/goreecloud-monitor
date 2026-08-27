from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from monitoring.engine import CheckOutcome, _apply_outcome, check_dns, check_push
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

    async def test_dns_monitor_uses_validated_explicit_resolver(self):
        monitor = Monitor(
            name="resolver-specific",
            kind=Monitor.Kind.DNS,
            target="dns://1.1.1.1/example.test",
            dns_record_type="A",
            expected_dns_answer="203.0.113.10",
            interval_seconds=60,
            timeout_seconds=10,
        )
        resolver = MagicMock()
        resolver.resolve = AsyncMock(return_value=["203.0.113.10"])
        with (
            patch("monitoring.engine.resolve_and_validate_network_target", new=AsyncMock(return_value=["1.1.1.1"])) as validate,
            patch("monitoring.engine.dns.asyncresolver.Resolver", return_value=resolver) as resolver_factory,
        ):
            outcome = await check_dns(monitor)

        self.assertTrue(outcome.success)
        validate.assert_awaited_once_with("1.1.1.1", 53)
        resolver_factory.assert_called_once_with(configure=False)
        self.assertEqual(resolver.nameservers, ["1.1.1.1"])
        self.assertEqual(resolver.port, 53)
        self.assertEqual(resolver.lifetime, 10.0)
        resolver.resolve.assert_awaited_once_with("example.test", "A")

    async def test_dns_monitor_keeps_system_resolver_for_plain_target(self):
        monitor = Monitor(
            name="system-resolver",
            kind=Monitor.Kind.DNS,
            target="example.test",
            dns_record_type="AAAA",
            interval_seconds=60,
            timeout_seconds=10,
        )
        resolver = MagicMock()
        resolver.resolve = AsyncMock(return_value=["2001:db8::10"])
        with (
            patch("monitoring.engine.resolve_and_validate_network_target", new=AsyncMock()) as validate,
            patch("monitoring.engine.dns.asyncresolver.Resolver", return_value=resolver) as resolver_factory,
        ):
            outcome = await check_dns(monitor)

        self.assertTrue(outcome.success)
        validate.assert_not_awaited()
        resolver_factory.assert_called_once_with()
        resolver.resolve.assert_awaited_once_with("example.test", "AAAA")
