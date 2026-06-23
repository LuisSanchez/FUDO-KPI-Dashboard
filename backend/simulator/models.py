from django.db import models


class UserSessionData(models.Model):
    """Per-user ephemeral storage for uploaded file data, keyed by Django session."""

    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    sales_df_pickle = models.BinaryField(null=True, blank=True)
    expenses_df_pickle = models.BinaryField(null=True, blank=True)
    products = models.JSONField(default=list)
    sales_months = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "simulator_user_session"


class SavedScenario(models.Model):
    """Named snapshot of session sales/expenses for multi-month comparison."""

    session_key = models.CharField(max_length=40, db_index=True)
    name = models.CharField(max_length=120)
    month = models.CharField(max_length=7, blank=True, default="")  # YYYY-MM or ""
    note = models.CharField(max_length=255, blank=True, default="")
    sales_df_pickle = models.BinaryField(null=True, blank=True)
    expenses_df_pickle = models.BinaryField(null=True, blank=True)
    products = models.JSONField(default=list)
    sales_months = models.JSONField(default=list)
    kpi_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "simulator_saved_scenario"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["session_key", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.session_key[:8]}…)"
