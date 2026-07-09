"""Главная, статичные страницы, FAQ, калькулятор."""
from django.shortcuts import render, get_object_or_404
from catalog.models import Product
from .models import StaticPage, FAQ


def home(request):
    popular = list(Product.objects.filter(is_active=True, is_popular=True).select_related("category").prefetch_related("labels")[:4])
    for p in popular:
        if p.old_price and p.old_price > p.price:
            p.discount = round((float(p.old_price) - float(p.price)) / float(p.old_price) * 100)
            p.saving = int(float(p.old_price) - float(p.price))
        else:
            p.discount = None
            p.saving = None
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, "home.html", {"popular_products": popular, "faqs": faqs})


def static_page(request, slug):
    page = get_object_or_404(StaticPage, slug=slug, is_active=True)
    return render(request, "page.html", {"page": page})


def calculator(request):
    from itertools import groupby
    qs = (Product.objects.filter(is_active=True).select_related("category")
          .order_by("category__name", "name"))
    groups = [(cat, list(items)) for cat, items in groupby(qs, key=lambda p: p.category.name)]
    return render(request, "calculator.html", {"calc_groups": groups})
