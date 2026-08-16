from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from monitoring.models import CheckResult


class Command(BaseCommand):
    help = "Delete check evidence older than the configured retention period"

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=settings.MONITOR_CHECK_RETENTION_DAYS)
        deleted, _ = CheckResult.objects.filter(checked_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired check-result row(s)"))
