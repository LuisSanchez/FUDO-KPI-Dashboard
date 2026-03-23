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
