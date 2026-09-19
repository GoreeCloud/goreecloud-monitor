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
from monitoring.retention import prune_monitor_history

logger = logging.getLogger("monitoring.access")


class Command(BaseCommand):
    help = "Run the GoreeCloud Monitor asynchronous check worker"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run one due-check pass and exit")

    def handle(self, *args, **options):
        log_event(logger, "worker.started", once=bool(options["once"]), max_concurrency=settings.MONITOR_MAX_CONCURRENCY)
        self.stdout.write(self.style.SUCCESS("GoreeCloud Monitor worker started"))
        last_history_prune = None
        try:
            while True:
                close_old_connections()
                now = timezone.now()
                monotonic_now = time.monotonic()
                if (
                    last_history_prune is None
                    or monotonic_now - last_history_prune
                    >= settings.MONITOR_HISTORY_PRUNE_INTERVAL_SECONDS
                ):
                    try:
                        result = prune_monitor_history(now=now)
                    except Exception as exc:
                        log_event(
                            logger,
                            "worker.history_prune_failed",
                            level=logging.ERROR,
                            exception_type=type(exc).__name__,
                        )
                    else:
                        if result.check_results_deleted or result.job_events_deleted:
                            log_event(
                                logger,
                                "worker.history_pruned",
                                check_results=result.check_results_deleted,
                                job_events=result.job_events_deleted,
                                check_retention_days=settings.MONITOR_CHECK_RETENTION_DAYS,
                                job_event_retention_days=settings.MONITOR_JOB_EVENT_RETENTION_DAYS,
                            )
                    last_history_prune = monotonic_now
                monitor_ids = [m.id for m in Monitor.objects.filter(enabled=True).only("id", "last_checked_at", "interval_seconds") if m.is_due(now)]
                asyncio.run(run_batch(monitor_ids))
                if options["once"]:
                    break
                time.sleep(settings.MONITOR_POLL_SECONDS)
        finally:
            log_event(logger, "worker.stopped", once=bool(options["once"]))
