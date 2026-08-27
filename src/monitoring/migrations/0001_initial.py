# Generated for GoreeCloud Monitor 0.1.0.
import monitoring.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Monitor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, unique=True)),
                ("kind", models.CharField(choices=[("HTTPS", "HTTPS"), ("HTTP", "HTTP"), ("TCP", "TCP"), ("DNS", "DNS"), ("PUSH", "Push / heartbeat")], max_length=8)),
                ("target", models.CharField(blank=True, max_length=2048)),
                ("port", models.PositiveIntegerField(blank=True, null=True)),
                ("enabled", models.BooleanField(default=True)),
                ("interval_seconds", models.PositiveIntegerField(default=60)),
                ("timeout_seconds", models.PositiveIntegerField(default=10)),
                ("failure_threshold", models.PositiveIntegerField(default=2)),
                ("recovery_threshold", models.PositiveIntegerField(default=1)),
                ("http_method", models.CharField(default="GET", max_length=8)),
                ("expected_status_code", models.PositiveIntegerField(default=200)),
                ("follow_redirects", models.BooleanField(default=True)),
                ("expected_body_text", models.CharField(blank=True, max_length=500)),
                ("expected_json_path", models.CharField(blank=True, max_length=200)),
                ("expected_json_value", models.CharField(blank=True, max_length=500)),
                ("tls_warning_days", models.PositiveIntegerField(default=14)),
                ("dns_record_type", models.CharField(default="A", max_length=8)),
                ("expected_dns_answer", models.CharField(blank=True, max_length=500)),
                ("heartbeat_token", models.CharField(default=monitoring.models.generate_heartbeat_token, max_length=64, unique=True)),
                ("heartbeat_grace_seconds", models.PositiveIntegerField(default=60)),
                ("last_heartbeat_at", models.DateTimeField(blank=True, null=True)),
                ("state", models.CharField(choices=[("UNKNOWN", "Unknown"), ("UP", "Up"), ("DOWN", "Down"), ("DEGRADED", "Degraded"), ("PAUSED", "Paused"), ("MAINTENANCE", "Maintenance")], default="UNKNOWN", max_length=16)),
                ("consecutive_failures", models.PositiveIntegerField(default=0)),
                ("consecutive_successes", models.PositiveIntegerField(default=0)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("last_success_at", models.DateTimeField(blank=True, null=True)),
                ("last_failure_at", models.DateTimeField(blank=True, null=True)),
                ("response_time_ms", models.FloatField(blank=True, null=True)),
                ("tls_expires_at", models.DateTimeField(blank=True, null=True)),
                ("last_message", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="CheckResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("checked_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("success", models.BooleanField()),
                ("observed_state", models.CharField(choices=[("UNKNOWN", "Unknown"), ("UP", "Up"), ("DOWN", "Down"), ("DEGRADED", "Degraded"), ("PAUSED", "Paused"), ("MAINTENANCE", "Maintenance")], max_length=16)),
                ("response_time_ms", models.FloatField(blank=True, null=True)),
                ("message", models.CharField(blank=True, max_length=500)),
                ("monitor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="checks", to="monitoring.monitor")),
            ],
            options={"ordering": ["-checked_at"]},
        ),
        migrations.CreateModel(
            name="Incident",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("failure_reason", models.CharField(blank=True, max_length=500)),
                ("recovery_message", models.CharField(blank=True, max_length=500)),
                ("monitor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incidents", to="monitoring.monitor")),
            ],
            options={"ordering": ["-started_at"]},
        ),
        migrations.CreateModel(
            name="MaintenanceWindow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("monitors", models.ManyToManyField(related_name="maintenance_windows", to="monitoring.monitor")),
            ],
            options={"ordering": ["-starts_at"]},
        ),
        migrations.AddIndex(model_name="monitor", index=models.Index(fields=["enabled", "last_checked_at"], name="mon_enabled_checked_idx")),
        migrations.AddIndex(model_name="monitor", index=models.Index(fields=["state"], name="mon_state_idx")),
        migrations.AddIndex(model_name="checkresult", index=models.Index(fields=["monitor", "-checked_at"], name="check_monitor_checked_idx")),
        migrations.AddIndex(model_name="incident", index=models.Index(fields=["ended_at", "started_at"], name="incident_open_started_idx")),
    ]
