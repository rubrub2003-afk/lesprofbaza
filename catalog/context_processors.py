"""Меню категорий, счётчик корзины и данные для живого поиска — во всех шаблонах."""
from .models import Category, Product


def catalog_menu(request):
    groups = (Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related("children"))
    cart = request.session.get("cart", {})
    cart_count = sum(cart.values()) if cart else 0

    def money(p):
        return "{:,}".format(int(p.price)).replace(",", " ") + " " + p.get_unit_display()

    search_items = [{"n": p.name, "u": p.get_absolute_url(), "p": money(p)}
                    for p in Product.objects.filter(is_active=True).only("name", "slug", "price", "unit")]
    search_cats = [{"n": g.name, "u": g.get_absolute_url()} for g in groups]
    return {"catalog_groups": groups, "cart_count": cart_count,
            "search_items": search_items, "search_cats": search_cats}
