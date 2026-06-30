from django.contrib import admin
from .models import Order, OrderItem, Lead


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "receive", "short_comment", "total", "status", "created")
    list_filter = ("status", "receive", "created")
    list_editable = ("status",)
    search_fields = ("name", "phone", "email")
    inlines = [OrderItemInline]

    @admin.display(description="Комментарий")
    def short_comment(self, obj):
        if not obj.comment:
            return "—"
        return (obj.comment[:50] + "…") if len(obj.comment) > 50 else obj.comment
    readonly_fields = ("created",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("kind", "phone", "name", "product", "processed", "created")
    list_filter = ("kind", "processed", "created")
    list_editable = ("processed",)
    search_fields = ("phone", "name")
