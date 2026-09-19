from django.db import migrations, models


def forward_noop(apps, schema_editor):
    pass


def pause_oncalendar_for_rollback(apps, schema_editor):
    Monitor = apps.get_model("monitoring", "Monitor")
    for monitor in Monitor.objects.filter(kind="JOB", job_schedule_mode="ONCAL"):
        expression = (monitor.job_cron_expression or "").strip()
        message = f"Rollback paused former OnCalendar schedule: {expression}"[:500]
        Monitor.objects.filter(pk=monitor.pk).update(
            job_schedule_mode="SIMPLE",
            job_cron_expression="",
            enabled=False,
            state="PAUSED",
            last_message=message,
        )


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0005_job_event_idempotency")]

    operations = [
        migrations.AlterField(
            model_name="monitor",
            name="job_schedule_mode",
            field=models.CharField(
                choices=[
                    ("SIMPLE", "Simple interval"),
                    ("CRON", "Cron schedule"),
                    ("ONCAL", "systemd OnCalendar"),
                ],
                default="SIMPLE",
                max_length=8,
            ),
        ),
        migrations.RunPython(forward_noop, pause_oncalendar_for_rollback),
    ]
