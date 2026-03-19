import logging

from django.conf import settings
from django.core.checks import Warning, register
from django.db.utils import OperationalError, ProgrammingError


@register(database=True)
def check_socialapp_for_site(app_configs, **kwargs):
    try:
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp

        site = Site.objects.filter(id=settings.SITE_ID).first()
        if not site:
            return [
                Warning(
                    "SITE_ID does not exist in django_site.",
                    hint=f"SITE_ID={settings.SITE_ID}",
                    id="kudea.W001",
                )
            ]

        has_social_app = SocialApp.objects.filter(sites__id=site.id).exists()
        if not has_social_app:
            return [
                Warning(
                    "SITE_ID has no SocialApp associated.",
                    hint=(
                        f"SITE_ID={site.id} domain={site.domain}."
                        " Social login will redirect to /accounts/login/."
                    ),
                    id="kudea.W002",
                )
            ]
    except (OperationalError, ProgrammingError):
        return []
    except Exception:
        logging.getLogger(__name__).exception("SocialApp site check failed.")
        return []

    return []
