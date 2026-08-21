from unittest.mock import AsyncMock, patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from monitoring.engine import check_ping
from monitoring.migration import map_kuma_monitor
from monitoring.models import Monitor


class PingModelTests(SimpleTestCase):
    def test_ping_monitor_accepts_hostname_without_port(self):
        monitor = Monitor(name="ping", kind=Monitor.Kind.PING, target="vps.internal", port=None, timeout_seconds=3)
        monitor.full_clean(exclude=["heartbeat_token"], validate_unique=False)

    def test_ping_monitor_rejects_url_or_port(self):
        for target, port in (("https://example.com", None), ("example.com", 443)):
            monitor = Monitor(name="bad-ping", kind=Monitor.Kind.PING, target=target, port=port, timeout_seconds=3)
            with self.assertRaises(ValidationError):
                monitor.full_clean(exclude=["heartbeat_token"], validate_unique=False)


class PingEngineTests(SimpleTestCase):
    async def test_ping_uses_policy_validated_numeric_destination(self):
        monitor = Monitor(name="ping", kind=Monitor.Kind.PING, target="vps.internal", timeout_seconds=3)
        with (
            patch("monitoring.engine.resolve_and_validate_network_target", new=AsyncMock(return_value=["100.64.0.10"])) as resolve,
            patch("monitoring.engine.icmp_echo", new=AsyncMock(return_value=12.5)) as echo,
        ):
            outcome = await check_ping(monitor)
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.observed_state, Monitor.State.UP)
        self.assertEqual(outcome.response_time_ms, 12.5)
        resolve.assert_awaited_once_with("vps.internal", 0)
        echo.assert_awaited_once()
        self.assertEqual(echo.await_args.args[0], "100.64.0.10")

    async def test_ping_fails_without_disclosing_destination_when_echo_times_out(self):
        monitor = Monitor(name="ping", kind=Monitor.Kind.PING, target="private.example", timeout_seconds=1)
        with (
            patch("monitoring.engine.resolve_and_validate_network_target", new=AsyncMock(return_value=["100.64.0.11"])),
            patch("monitoring.engine.icmp_echo", new=AsyncMock(side_effect=TimeoutError())),
        ):
            outcome = await check_ping(monitor)
        self.assertFalse(outcome.success)
        self.assertEqual(outcome.observed_state, Monitor.State.DOWN)
        self.assertNotIn("100.64.0.11", outcome.message)
        self.assertNotIn("private.example", outcome.message)


class PingMigrationTests(SimpleTestCase):
    def test_uptime_kuma_ping_maps_to_native_ping_monitor(self):
        mapped = map_kuma_monitor(
            {
                "name": "GoreeCloud VPS",
                "type": "ping",
                "hostname": "100.64.0.10",
                "interval": 60,
                "timeout": 5,
                "maxretries": 0,
            }
        )
        self.assertTrue(mapped.supported)
        self.assertEqual(mapped.values["kind"], Monitor.Kind.PING)
        self.assertEqual(mapped.values["target"], "100.64.0.10")
        self.assertIsNone(mapped.values["port"])
