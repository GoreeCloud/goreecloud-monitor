import asyncio
import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from monitoring.engine import run_batch
from monitoring.models import Monitor
from monitoring.observability import log_event

logger = logging.getLogger("monitoring.access")


class Command(BaseCommand):
    help = "Run the GoreeCloud Monitor asynchronous check worker"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run one due-check pass and exit")

    def handle(self, *args, **options):
        log_event(logger, "worker.started", once=bool(options["once"]), max_concurrency=settings.MONITOR_MAX_CONCURRENCY)
        self.stdout.write(self.style.SUCCESS("GoreeCloud Monitor worker started"))
        try:
            while True:
                close_old_connections()
                now = timezone.now()
                monitor_ids = [m.id for m in Monitor.objects.filter(enabled=True).only("id", "last_checked_at", "interval_seconds") if m.is_due(now)]
                if monitor_ids:
                    asyncio.run(run_batch(monitor_ids))
                if options["once"]:
                    break
                time.sleep(settings.MONITOR_POLL_SECONDS)
        finally:
            log_event(logger, "worker.stopped", once=bool(options["once"]))
