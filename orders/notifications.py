"""Уведомления о новом заказе: почта + Telegram. Тихо игнорируем, если не настроено."""
import json
import urllib.request
from django.conf import settings
from django.core.mail import send_mail


def _order_text(order):
    lines = [f"Новый заказ №{order.pk} — {order.name}, {order.phone}",
             f"Получение: {order.get_receive_display()}"]
    if order.address:
        lines.append(f"Адрес: {order.address}")
    if order.comment:
        lines.append(f"Комментарий: {order.comment}")
    lines.append("Позиции:")
    for it in order.items.all():
        lines.append(f"  • {it.name} — {it.qty} × {it.price} = {it.line_total} ₽")
    lines.append(f"Итого (предв.): {order.total} ₽")
    return "\n".join(lines)


def send_order_notification(order):
    text = _order_text(order)
    # E-mail
    try:
        if settings.ORDER_NOTIFY_EMAIL:
            send_mail(f"Новый заказ №{order.pk}", text,
                      settings.EMAIL_HOST_USER or "noreply@lesprofbaza.ru",
                      [settings.ORDER_NOTIFY_EMAIL], fail_silently=True)
    except Exception:
        pass
    # Telegram
    try:
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": settings.TELEGRAM_CHAT_ID, "text": text}).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass
