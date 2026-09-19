from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0003_notification_outbox")]

    operations = [
        migrations.AlterField(
            model_name="monitor",
            name="kind",
            field=models.CharField(
                choices=[
                    ("HTTPS", "HTTPS"),
                    ("HTTP", "HTTP"),
                    ("TCP", "TCP"),
                    ("PING", "Ping / ICMP"),
                    ("DNS", "DNS"),
                    ("PUSH", "Push / heartbeat"),
                    ("JOB", "Scheduled job / dead-man"),
                ],
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="monitor",
            name="job_schedule_mode",
            field=models.CharField(
                choices=[("SIMPLE", "Simple interval"), ("CRON", "Cron schedule")],
                default="SIMPLE",
                max_length=8,
            ),
        ),
        migrations.AddField(model_name="monitor", name="job_cron_expression", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="monitor", name="job_timezone", field=models.CharField(default="UTC", max_length=64)),
        migrations.AddField(model_name="monitor", name="job_grace_seconds", field=models.PositiveIntegerField(default=60)),
        migrations.AddField(model_name="monitor", name="job_max_runtime_seconds", field=models.PositiveIntegerField(default=0)),
        migrations.CreateModel(
            name="JobEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("received_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("event_type", models.CharField(choices=[("START", "Start"), ("SUCCESS", "Success"), ("FAILURE", "Failure"), ("LOG", "Log")], max_length=16)),
                ("run_id", models.CharField(blank=True, max_length=128)),
                ("exit_code", models.IntegerField(blank=True, null=True)),
                ("duration_ms", models.FloatField(blank=True, null=True)),
                ("message", models.CharField(blank=True, max_length=500)),
                ("monitor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="job_events", to="monitoring.monitor")),
            ],
            options={"ordering": ["-received_at", "-id"]},
        ),
        migrations.AddIndex(
            model_name="jobevent",
            index=models.Index(fields=["monitor", "-received_at"], name="jobevent_monitor_time_idx"),
        ),
    ]
