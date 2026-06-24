from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    Google-authenticated user profile (additive — does not replace session storage).
    Links Django auth.User to Google subject id for OAuth login.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    google_id = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.EmailField(db_index=True)
    display_name = models.CharField(max_length=255, blank=True, default="")
    avatar_url = models.URLField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "simulator_user_profile"

    def __str__(self):
        return self.email or self.google_id


class UserSessionData(models.Model):
    """Per-user ephemeral storage for uploaded file data, keyed by Django session."""

    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    # Optional link when user is logged in (additive; existing rows keep user=NULL).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="session_data",
    )
    sales_df_pickle = models.BinaryField(null=True, blank=True)
    expenses_df_pickle = models.BinaryField(null=True, blank=True)
    products = models.JSONField(default=list)
    sales_months = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "simulator_user_session"
