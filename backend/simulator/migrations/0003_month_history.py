from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0002_userprofile_and_session_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersessiondata",
            name="month_history",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
