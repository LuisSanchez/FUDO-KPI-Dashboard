from django.conf import settings
from django.db import models


class UserSessionData(models.Model):
    """Per-user ephemeral storage for uploaded file data, keyed by Django session."""

    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="simulator_sessions",
    )
    sales_df_pickle = models.BinaryField(null=True, blank=True)
    expenses_df_pickle = models.BinaryField(null=True, blank=True)
    products = models.JSONField(default=list)
    sales_months = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "simulator_user_session"


class UserProfile(models.Model):
    """Google OAuth profile linked to Django auth user (additive)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    google_id = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(db_index=True)
    display_name = models.CharField(max_length=255, blank=True, default="")
    avatar_url = models.URLField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "simulator_user_profile"

    def __str__(self):
        return self.email or self.google_id
