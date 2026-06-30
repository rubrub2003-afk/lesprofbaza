"""Главная, статичные страницы, FAQ, калькулятор."""
from django.shortcuts import render, get_object_or_404
from catalog.models import Product
from .models import StaticPage, FAQ


def home(request):
    popular = list(Product.objects.filter(is_active=True, is_popular=True).prefetch_related("labels")[:8])
    for p in popular:
        if p.old_price and p.old_price > p.price:
            p.discount = round((float(p.old_price) - float(p.price)) / float(p.old_price) * 100)
        else:
            p.discount = None
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, "home.html", {"popular_products": popular, "faqs": faqs})


def static_page(request, slug):
    page = get_object_or_404(StaticPage, slug=slug, is_active=True)
    return render(request, "page.html", {"page": page})


def calculator(request):
    from itertools import groupby
    m3 = (Product.objects.filter(unit="m3", thickness__isnull=False, width__isnull=False,
                                 length__isnull=False, is_active=True)
          .select_related("category").order_by("category__name", "thickness", "width"))
    groups = [(cat, list(items)) for cat, items in groupby(m3, key=lambda p: p.category.name)]
    return render(request, "calculator.html", {"calc_groups": groups})
