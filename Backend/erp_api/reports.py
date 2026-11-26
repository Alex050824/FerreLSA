from urllib.parse import urlsplit

from django.conf import settings

from .http import endpoint, response


def _power_bi_embed_url(value):
    """Only return HTTPS Power BI report embed links, never arbitrary iframe URLs."""
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and parsed.hostname == "app.powerbi.com"
            and parsed.path in ("/view", "/reportEmbed")
            and bool(parsed.query)
            and not parsed.username
            and not parsed.password
        )
    except ValueError:
        return False


@endpoint("GET", access="ADMIN")
def power_bi_report(request):
    configured_url = settings.POWER_BI_REPORT_URL
    if not configured_url:
        return response({"configured": False, "url": ""})
    if not _power_bi_embed_url(configured_url):
        return response({"configured": False, "url": "", "invalid": True})
    return response({"configured": True, "url": configured_url})
