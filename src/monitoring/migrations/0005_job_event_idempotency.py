from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0004_scheduled_job_monitor")]

    operations = [
        migrations.AddField(
            model_name="jobevent",
            name="event_id",
            field=models.CharField(blank=True, max_length=36),
        ),
        migrations.AddConstraint(
            model_name="jobevent",
            constraint=models.UniqueConstraint(
                condition=~models.Q(event_id=""),
                fields=("monitor", "event_id"),
                name="jobevent_mon_eventid_uniq",
            ),
        ),
    ]
