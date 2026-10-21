from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("simulator", "0004_month_assumption"),
    ]

    operations = [
        migrations.CreateModel(
            name="AiSettings",
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
                ("provider", models.CharField(default="openrouter", max_length=20)),
                ("openrouter_model", models.CharField(blank=True, default="", max_length=120)),
                ("ollama_model", models.CharField(blank=True, default="", max_length=120)),
                ("ollama_base_url", models.CharField(blank=True, default="", max_length=300)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "simulator_ai_settings",
            },
        ),
    ]
