from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0001_initial")]

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
                ],
                max_length=8,
            ),
        ),
    ]
