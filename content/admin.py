from django.contrib import admin
from .models import SiteSettings, FAQ, StaticPage


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Компания", {"fields": ("company_name", "slogan")}),
        ("Контакты", {"fields": ("phone", "phone2", "email", "address", "hours")}),
        ("Мессенджеры и соцсети", {"fields": ("whatsapp", "telegram", "max_link", "instagram", "tg_bot")}),
        ("Доставка и карта", {"fields": ("free_delivery_m3", "map_embed", "yandex_maps_url")}),
        ("Отзывы и рейтинг", {"fields": ("show_product_reviews", "show_product_rating", "show_company_reviews")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "is_active")
    list_editable = ("order", "is_active")


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active", "updated")
    prepopulated_fields = {"slug": ("title",)}
