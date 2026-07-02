"""Счётчики новых заказов/заявок — только для страниц админки (красная точка)."""
from .models import Order, Lead
from catalog.models import Review


def admin_badges(request):
    if not request.path.startswith("/admin"):
        return {}
    if not getattr(request, "user", None) or not request.user.is_staff:
        return {}
    return {
        "admin_new_orders": Order.objects.filter(status="new").count(),
        "admin_new_leads": Lead.objects.filter(processed=False).count(),
        "admin_new_reviews": Review.objects.filter(is_approved=False).count(),
    }
