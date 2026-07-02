"""Корневая маршрутизация проекта ЛЕСПРОФБАЗА."""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from orders.views import admin_stats, clear_actions

admin.site.site_header = "ЛЕСПРОФБАЗА — управление сайтом"
admin.site.site_title = "ЛЕСПРОФБАЗА"
admin.site.index_title = "Панель управления"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("staff/stats/", admin_stats, name="admin_stats"),
    path("staff/clear-actions/", clear_actions, name="clear_actions"),
    path("", include("content.urls")),     # главная, статичные страницы, FAQ, калькулятор
    path("catalog/", include("catalog.urls")),
    path("", include("orders.urls")),       # корзина, оформление, заявки, кабинет
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
