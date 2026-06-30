"""Настройки сайта (контакты, тумблеры), FAQ, статичные страницы."""
from django.db import models


class SiteSettings(models.Model):
    """Глобальные настройки. Singleton — одна запись (load())."""
    company_name = models.CharField("Название", max_length=120, default="ЛЕСПРОФБАЗА")
    slogan = models.CharField("Девиз", max_length=160, default="Довольный клиент — наша задача!")

    phone = models.CharField("Телефон", max_length=40, blank=True)
    phone2 = models.CharField("Запасной телефон", max_length=40, blank=True)
    email = models.EmailField("E-mail", blank=True)
    address = models.CharField("Адрес / самовывоз", max_length=300, blank=True)
    hours = models.CharField("Часы работы", max_length=120, blank=True, default="Ежедневно, 8:00–20:00")

    whatsapp = models.CharField("WhatsApp (ссылка/номер)", max_length=200, blank=True)
    telegram = models.CharField("Telegram (ссылка)", max_length=200, blank=True)
    max_link = models.CharField("MAX (ссылка)", max_length=200, blank=True)
    instagram = models.CharField("Instagram (ссылка)", max_length=200, blank=True)
    tg_bot = models.CharField("Telegram-бот (ссылка)", max_length=200, blank=True)

    free_delivery_m3 = models.DecimalField("Бесплатная доставка от, м³", max_digits=6,
                                           decimal_places=2, null=True, blank=True)
    map_embed = models.TextField("Код карты (iframe Яндекс/OSM)", blank=True)
    yandex_maps_url = models.CharField("Ссылка «Открыть в Яндекс.Картах»", max_length=300, blank=True)

    # тумблеры отображения
    show_product_reviews = models.BooleanField("Показывать отзывы на товары", default=True)
    show_product_rating = models.BooleanField("Показывать рейтинг товаров", default=True)
    show_company_reviews = models.BooleanField("Показывать отзывы о компании", default=False)

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class FAQ(models.Model):
    question = models.CharField("Вопрос", max_length=250)
    answer = models.TextField("Ответ")
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показывать", default=True)

    class Meta:
        verbose_name = "Вопрос-ответ (FAQ)"
        verbose_name_plural = "Частые вопросы (FAQ)"
        ordering = ["order"]

    def __str__(self):
        return self.question


class StaticPage(models.Model):
    slug = models.SlugField("Адрес (slug)", max_length=80, unique=True,
                            help_text="Напр.: o-kompanii, dostavka-i-oplata, dlya-yurlic")
    title = models.CharField("Заголовок", max_length=200)
    body = models.TextField("Содержимое (HTML)", blank=True)
    is_active = models.BooleanField("Показывать", default=True)
    updated = models.DateTimeField("Изменена", auto_now=True)

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы (О компании, Доставка и т.д.)"

    def __str__(self):
        return self.title
