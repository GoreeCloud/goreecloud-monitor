from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0002_monitor_ping_kind")]

    operations = [
        migrations.CreateModel(
            name="NotificationOutbox",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("transition", models.CharField(max_length=16)),
                ("payload", models.JSONField()),
                ("idempotency_key", models.CharField(max_length=80, unique=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "next_attempt_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                ("last_attempt_at", models.DateTimeField(blank=True, null=True)),
                ("attempt_count", models.PositiveIntegerField(default=0)),
                (
                    "delivered_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        null=True,
                    ),
                ),
                ("last_failure_reason", models.CharField(blank=True, max_length=64)),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="notificationoutbox",
            index=models.Index(
                fields=["delivered_at", "next_attempt_at"],
                name="notify_outbox_due_idx",
            ),
        ),
    ]
