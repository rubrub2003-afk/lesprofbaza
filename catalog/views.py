"""Каталог: список с фильтрами, категория, карточка товара, поиск (API)."""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.shortcuts import redirect
from .models import Category, Product, Review, Label, Species


def _decorate(products):
    out = list(products)
    for p in out:
        if p.old_price and p.old_price > p.price:
            p.discount = round((float(p.old_price) - float(p.price)) / float(p.old_price) * 100)
            p.saving = int(float(p.old_price) - float(p.price))
        else:
            p.discount = None
            p.saving = None
    return out


def _render_list(request, category=None, title="Каталог пиломатериалов"):
    qs = Product.objects.filter(is_active=True).select_related("category", "category__parent").prefetch_related("labels")
    if category is not None:
        if category.is_group:
            qs = qs.filter(category__parent=category)
        else:
            qs = qs.filter(category=category)
    qs = qs.order_by("-is_popular", "category", "name")
    used = set(qs.values_list("species", flat=True))
    sp_names = {"pine_spruce": "Сосна / ель (хвоя)"}
    species_list = [(code, sp_names.get(code, name)) for code, name in Species.choices if code in used]
    std_order = ["ГОСТ", "ТУ", "Камерная сушка"]
    stds = sorted({s for s in qs.values_list("standard", flat=True) if s},
                  key=lambda x: std_order.index(x) if x in std_order else 99)
    # Фиксированные списки фильтров — показываем всегда (даже если по некоторым нет товаров)
    sorts_list = ["1-й сорт", "2-й сорт", "Экстра", "Прима",
                  "A", "B", "C", "D", "AB", "BC", "CD"]
    types_list = ["Сучковый", "Без сучковый", "Цельноламельная", "Сращенная"]
    return render(request, "catalog/list.html", {
        "title": title, "products": _decorate(qs), "current_category": category,
        "labels": Label.objects.all(), "species_list": species_list,
        "standards_list": stds, "sorts_list": sorts_list, "types_list": types_list,
    })


def catalog_index(request):
    return _render_list(request)


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    return _render_list(request, category=category, title=category.name)


def product_view(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category", "category__parent").prefetch_related("labels", "images", "reviews"),
        slug=slug, is_active=True)
    if product.old_price and product.old_price > product.price:
        product.discount = round((float(product.old_price) - float(product.price)) / float(product.old_price) * 100)
    else:
        product.discount = None
    related = _decorate(Product.objects.filter(category=product.category, is_active=True)
                        .exclude(pk=product.pk).prefetch_related("labels")[:4])
    reviews = product.reviews.filter(is_approved=True)
    return render(request, "catalog/product.html", {
        "product": product, "related": related, "reviews": reviews,
    })


def search(request):
    q = (request.GET.get("q") or "").strip().lower()
    if not q:
        return JsonResponse({"categories": [], "products": []})

    tokens = q.split()

    def starts(name):
        low = name.lower()
        words = low.replace("×", " ").split()
        return all(t in low or any(w.startswith(t) for w in words) for t in tokens)

    cats = [{"name": c.name, "url": c.get_absolute_url()}
            for c in Category.objects.filter(parent__isnull=True, is_active=True) if starts(c.name)]
    prods = [{"name": p.name, "url": p.get_absolute_url(),
              "price": f"{p.price:n} {p.get_unit_display()}"}
             for p in Product.objects.filter(is_active=True) if starts(p.name)][:6]
    return JsonResponse({"categories": cats, "products": prods})


def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if request.method == "POST":
        author = (request.POST.get("author") or "").strip()
        text = (request.POST.get("text") or "").strip()
        try:
            rating = int(request.POST.get("rating", 5))
        except ValueError:
            rating = 5
        if author and text:
            Review.objects.create(product=product, author=author, text=text,
                                  rating=max(1, min(5, rating)), is_approved=False)
    return redirect(product.get_absolute_url() + "?review=sent#reviews")


def compare_view(request):
    slugs = [x for x in (request.GET.get("items") or "").split(",") if x][:4]
    products = list(Product.objects.filter(slug__in=slugs, is_active=True).select_related("category"))
    products.sort(key=lambda p: slugs.index(p.slug) if p.slug in slugs else 0)
    return render(request, "catalog/compare.html", {"products": products})


def favorites_view(request):
    slugs = [x for x in (request.GET.get("items") or "").split(",") if x]
    products = _decorate(Product.objects.filter(slug__in=slugs, is_active=True)
                         .select_related("category").prefetch_related("labels"))
    products.sort(key=lambda p: slugs.index(p.slug) if p.slug in slugs else 0)
    return render(request, "catalog/favorites.html", {"products": products})
