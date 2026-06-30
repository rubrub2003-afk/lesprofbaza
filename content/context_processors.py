from .models import SiteSettings


def site_settings(request):
    """Настройки сайта доступны во всех шаблонах как {{ site }}."""
    return {"site": SiteSettings.load()}
