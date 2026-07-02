"""Заказы (корзина-заявка) и быстрые заявки (звонок / в 1 клик)."""
from django.db import models
from django.conf import settings


class Order(models.Model):
    STATUS = [
        ("new", "На рассмотрении"),
        ("in_progress", "В работе"),
        ("shipping", "Едет к вам"),
        ("done", "Доставлен"),
    ]
    RECEIVE = [
        ("pickup", "Самовывоз"),
        ("delivery", "Доставка"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Пользователь",
                             null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    name = models.CharField("Имя", max_length=120)
    phone = models.CharField("Телефон", max_length=40)
    email = models.EmailField("E-mail", blank=True)
    receive = models.CharField("Получение", max_length=10, choices=RECEIVE, default="pickup")
    address = models.CharField("Адрес доставки", max_length=300, blank=True)
    comment = models.TextField("Комментарий", blank=True)
    total = models.DecimalField("Сумма (предв.)", max_digits=12, decimal_places=2, default=0)
    status = models.CharField("Статус", max_length=12, choices=STATUS, default="new")
    created = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created"]

    def __str__(self):
        return f"Заказ №{self.pk} — {self.name} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", null=True, blank=True,
                                on_delete=models.SET_NULL, verbose_name="Товар")
    name = models.CharField("Наименование", max_length=200)
    size_text = models.CharField("Размер", max_length=80, blank=True)
    unit = models.CharField("Единица", max_length=10, blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField("Количество", default=1)
    line_total = models.DecimalField("Сумма строки", max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.name} × {self.qty}"


class Lead(models.Model):
    TYPES = [
        ("callback", "Заказать звонок"),
        ("quick", "Быстрый заказ"),
        ("consult", "Консультация / подбор"),
    ]
    kind = models.CharField("Тип", max_length=12, choices=TYPES, default="callback")
    name = models.CharField("Имя", max_length=120, blank=True)
    phone = models.CharField("Телефон", max_length=40)
    comment = models.TextField("Комментарий", blank=True)
    product = models.ForeignKey("catalog.Product", null=True, blank=True,
                                on_delete=models.SET_NULL, verbose_name="Товар")
    processed = models.BooleanField("Обработана", default=False)
    created = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки (звонки, быстрый заказ)"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.phone}"
