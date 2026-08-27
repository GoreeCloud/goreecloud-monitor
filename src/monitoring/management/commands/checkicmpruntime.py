import asyncio

from django.core.management.base import BaseCommand, CommandError

from monitoring.engine import check_ping
from monitoring.models import Monitor


class Command(BaseCommand):
    help = "Verify the worker can perform a low-privilege ICMP Echo check"

    def add_arguments(self, parser):
        parser.add_argument("--target", default="127.0.0.1", help="Approved hostname or IP address to probe")
        parser.add_argument("--timeout", type=int, default=3, help="Probe timeout in seconds")

    def handle(self, *args, **options):
        monitor = Monitor(
            name="icmp-runtime-proof",
            kind=Monitor.Kind.PING,
            target=options["target"],
            timeout_seconds=max(1, int(options["timeout"])),
            interval_seconds=max(5, int(options["timeout"])),
        )
        monitor.full_clean(exclude=["heartbeat_token"], validate_unique=False)
        outcome = asyncio.run(check_ping(monitor))
        if not outcome.success:
            raise CommandError(outcome.message or "ICMP runtime proof failed")
        latency = f"{outcome.response_time_ms:.2f} ms" if outcome.response_time_ms is not None else "available"
        self.stdout.write(self.style.SUCCESS(f"Low-privilege ICMP runtime proof passed ({latency})"))
