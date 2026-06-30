from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Label, Product, ProductImage, Review


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "order", "is_active")
    list_filter = ("is_active", "parent")
    list_editable = ("order", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {}  # slug генерируется автоматически


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "order")
    list_editable = ("color", "order")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "dimensions", "price_display",
                    "in_stock", "is_popular", "is_active")
    list_filter = ("category", "species", "in_stock", "is_popular", "is_active", "labels")
    list_editable = ("in_stock", "is_popular", "is_active")
    search_fields = ("name", "sku")
    filter_horizontal = ("labels",)
    inlines = [ProductImageInline]
    fieldsets = (
        ("Основное", {"fields": ("category", "name", "sku", "is_active", "is_popular")}),
        ("Характеристики", {"fields": ("species", "grade", "standard")}),
        ("Размеры", {"fields": ("thickness", "width", "length", "size_text")}),
        ("Цена и наличие", {"fields": ("unit", "price", "old_price", "in_stock")}),
        ("Контент", {"fields": ("description", "labels")}),
    )

    @admin.display(description="Цена")
    def price_display(self, obj):
        return f"{obj.price:n} {obj.get_unit_display()}"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("author", "target", "rating", "is_approved", "created")
    list_filter = ("is_approved", "rating", "created")
    list_editable = ("is_approved",)
    search_fields = ("author", "text")
    actions = ["approve", "reject"]

    @admin.display(description="Кому")
    def target(self, obj):
        return obj.product.name if obj.product else "О компании"

    @admin.action(description="Одобрить (опубликовать)")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Снять с публикации")
    def reject(self, request, queryset):
        queryset.update(is_approved=False)
