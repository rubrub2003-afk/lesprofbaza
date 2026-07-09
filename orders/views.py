"""Корзина (сессия), оформление заказа, кабинет."""
from django.shortcuts import render, redirect, get_object_or_404
from catalog.models import Product
from .models import Order, OrderItem
from django.http import JsonResponse
from .models import Lead
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from .notifications import send_order_notification
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.models import LogEntry


def _digits(v):
    return "".join(ch for ch in (v or "") if ch.isdigit())


def _norm_phone(v):
    d = _digits(v)
    if len(d) == 11 and d[0] == "8":
        d = "7" + d[1:]
    elif len(d) == 10:
        d = "7" + d
    return d


def _cart_items(session):
    cart = session.get("cart", {})
    items, total = [], 0
    for slug, qty in cart.items():
        p = Product.objects.filter(slug=slug, is_active=True).first()
        if not p:
            continue
        lt = round(float(p.price) * qty)
        items.append({"product": p, "qty": qty, "line_total": lt})
        total += lt
    return items, total


def cart(request):
    if request.method == "POST" and request.POST.get("action") == "checkout":
        # учитываем изменённые в корзине количества
        cart = request.session.get("cart", {})
        for slug in list(cart.keys()):
            val = request.POST.get("qty_" + slug)
            if val:
                try:
                    cart[slug] = max(1, int(val))
                except ValueError:
                    pass
        request.session["cart"] = cart
        items, total = _cart_items(request.session)
        if items:
            order = Order.objects.create(
                name=request.POST.get("name", ""), phone=request.POST.get("phone", ""),
                receive=request.POST.get("receive", "pickup"),
                address=request.POST.get("address", ""), comment=request.POST.get("comment", ""),
                total=total, user=request.user if request.user.is_authenticated else None)
            for it in items:
                p = it["product"]
                OrderItem.objects.create(order=order, product=p, name=p.name, size_text=p.size_text,
                                         unit=p.get_unit_display(), price=p.price,
                                         qty=it["qty"], line_total=it["line_total"])
            send_order_notification(order)
            request.session["cart"] = {}
            return render(request, "orders/cart.html", {"order": order, "success": True})
    items, total = _cart_items(request.session)
    return render(request, "orders/cart.html", {"items": items, "total": total})


def add_to_cart(request, slug):
    p = get_object_or_404(Product, slug=slug, is_active=True)
    try:
        qty = int(request.POST.get("qty") or request.GET.get("qty") or 1)
    except ValueError:
        qty = 1
    cart = request.session.get("cart", {})
    cart[slug] = cart.get(slug, 0) + max(1, qty)
    request.session["cart"] = cart
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "count": sum(cart.values())})
    return redirect("orders:cart")


def remove_from_cart(request, slug):
    cart = request.session.get("cart", {})
    cart.pop(slug, None)
    request.session["cart"] = cart
    return redirect("orders:cart")


def account(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).prefetch_related("items")
        active = orders.exclude(status="done").first()
        return render(request, "account/cabinet.html", {"orders": orders, "active": active})
    return render(request, "account/login.html")


def register(request):
    if request.method != "POST":
        return redirect("orders:account")
    name = (request.POST.get("name") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    email = (request.POST.get("email") or "").strip()
    password = request.POST.get("password") or ""
    username = _norm_phone(phone) or email
    if not username or len(password) < 4:
        return render(request, "account/login.html", {"error": "Укажите телефон и пароль (от 4 символов)", "tab": "reg"})
    if User.objects.filter(username=username).exists():
        return render(request, "account/login.html", {"error": "Такой аккаунт уже есть — войдите", "tab": "login"})
    u = User.objects.create_user(username=username, email=email, password=password, first_name=name)
    auth_login(request, u)
    return redirect("orders:account")


def login_view(request):
    if request.method != "POST":
        return redirect("orders:account")
    login_id = (request.POST.get("login") or "").strip()
    password = request.POST.get("password") or ""
    username = _norm_phone(login_id) or login_id
    user = authenticate(request, username=username, password=password)
    if user is None and "@" in login_id:
        u = User.objects.filter(email=login_id).first()
        if u:
            user = authenticate(request, username=u.username, password=password)
    if user is not None:
        auth_login(request, user)
        return redirect("orders:account")
    return render(request, "account/login.html", {"error": "Неверный телефон/почта или пароль", "tab": "login"})


def logout_view(request):
    auth_logout(request)
    return redirect("content:home")


def lead(request):
    """Заявка: заказать звонок / быстрый заказ. Создаёт Lead и шлёт уведомление."""
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)
    phone = (request.POST.get("phone") or "").strip()
    if not phone:
        return JsonResponse({"ok": False, "error": "Укажите телефон"}, status=400)
    product = None
    pslug = request.POST.get("product")
    if pslug:
        product = Product.objects.filter(slug=pslug).first()
    Lead.objects.create(
        kind=request.POST.get("kind", "callback"),
        name=request.POST.get("name", ""), phone=phone,
        comment=request.POST.get("comment", ""), product=product)
    return JsonResponse({"ok": True})


def reorder(request, pk):
    """Быстрый повтор заказа: переносит позиции прошлого заказа в корзину."""
    if not request.user.is_authenticated:
        return redirect("orders:account")
    order = get_object_or_404(Order, pk=pk, user=request.user)
    cart = request.session.get("cart", {})
    for it in order.items.select_related("product").all():
        p = it.product
        if not p:
            p = Product.objects.filter(name=it.name, is_active=True).first()
        if p and p.is_active:
            cart[p.slug] = cart.get(p.slug, 0) + it.qty
    request.session["cart"] = cart
    return redirect("orders:cart")


@staff_member_required
def admin_stats(request):
    """JSON-счётчики новых заказов/заявок для живого индикатора в админке."""
    from catalog.models import Review
    return JsonResponse({
        "orders": Order.objects.filter(status="new", admin_seen=False).count(),
        "leads": Lead.objects.filter(processed=False, admin_seen=False).count(),
        "reviews": Review.objects.filter(is_approved=False, admin_seen=False).count(),
    })


@staff_member_required
def mark_seen(request, kind):
    """Отметить новые заказы/заявки/отзывы как просмотренные (гасит красную точку)."""
    from catalog.models import Review
    if kind == "orders":
        Order.objects.filter(status="new", admin_seen=False).update(admin_seen=True)
    elif kind == "leads":
        Lead.objects.filter(processed=False, admin_seen=False).update(admin_seen=True)
    elif kind == "reviews":
        Review.objects.filter(is_approved=False, admin_seen=False).update(admin_seen=True)
    return JsonResponse({"ok": True})


@staff_member_required
def clear_actions(request):
    """Очистить журнал «Последние действия» для текущего сотрудника."""
    LogEntry.objects.filter(user=request.user).delete()
    return redirect("admin:index")
