"""Модели каталога ЛЕСПРОФБАЗА: категории, метки, товары, фото, отзывы."""
from django.db import models
from django.urls import reverse
import re
from django.utils.text import slugify


def ru_slug(value):
    return slugify(value, allow_unicode=True)


class Unit(models.TextChoices):
    M3 = "m3", "₽ / м³"
    M2 = "m2", "₽ / м²"
    PIECE = "pc", "₽ / шт"
    RM = "rm", "₽ / пог.м"
    SHEET = "sheet", "₽ / лист"


class Species(models.TextChoices):
    PINE_SPRUCE = "pine_spruce", "Сосна / ель"
    LINDEN = "linden", "Липа"
    LARCH = "larch", "Лиственница"
    OTHER = "other", "Другое"


class Category(models.Model):
    name = models.CharField("Название", max_length=120)
    slug = models.SlugField("Адрес (slug)", max_length=140, unique=True, blank=True, allow_unicode=True)
    parent = models.ForeignKey("self", verbose_name="Родительская категория", null=True, blank=True,
                               related_name="children", on_delete=models.CASCADE)
    description = models.CharField("Короткое описание", max_length=200, blank=True)
    image = models.ImageField("Фото категории", upload_to="categories/", blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показывать на сайте", default=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.parent} → {self.name}" if self.parent else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = ru_slug(self.name) or "kategoriya"
            slug, i = base, 2
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"; i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # ведём на каталог с авто-фильтром по разделу (галочка проставляется сама)
        return reverse("catalog:index") + "?cat=" + self.slug

    @property
    def is_group(self):
        return self.parent_id is None


class Label(models.Model):
    COLOR_CHOICES = [("pine", "Янтарный"), ("forest", "Зелёный"), ("dark", "Тёмный"), ("red", "Красный")]
    name = models.CharField("Текст метки", max_length=40)
    color = models.CharField("Цвет", max_length=10, choices=COLOR_CHOICES, default="pine")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Метка товара"
        verbose_name_plural = "Метки товаров"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, verbose_name="Категория", related_name="products", on_delete=models.PROTECT)
    name = models.CharField("Наименование", max_length=200)
    slug = models.SlugField("Адрес (slug)", max_length=220, unique=True, blank=True, allow_unicode=True)
    sku = models.CharField("Артикул", max_length=40, blank=True)
    species = models.CharField("Порода", max_length=20, choices=Species.choices, default=Species.PINE_SPRUCE)
    grade = models.CharField("Сорт", max_length=60, blank=True)
    standard = models.CharField("Стандарт", max_length=60, blank=True)
    thickness = models.PositiveIntegerField("Толщина, мм", null=True, blank=True)
    width = models.PositiveIntegerField("Ширина, мм", null=True, blank=True)
    length = models.PositiveIntegerField("Длина, мм", null=True, blank=True)
    size_text = models.CharField("Размер (текстом)", max_length=80, blank=True)
    unit = models.CharField("Единица цены", max_length=6, choices=Unit.choices, default=Unit.M3)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    old_price = models.DecimalField("Старая цена", max_digits=10, decimal_places=2, null=True, blank=True)
    in_stock = models.BooleanField("В наличии", default=True)
    description = models.TextField("Описание", blank=True)
    labels = models.ManyToManyField(Label, verbose_name="Метки", blank=True, related_name="products")
    is_popular = models.BooleanField("Показывать в «Популярном»", default=False)
    is_active = models.BooleanField("Показывать на сайте", default=True)
    created = models.DateTimeField("Добавлен", auto_now_add=True)
    updated = models.DateTimeField("Изменён", auto_now=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = ru_slug(self.name) or "tovar"
            slug, i = base, 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"; i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product", args=[self.slug])

    @property
    def image_path(self):
        """Статичная картинка-текстура по типу материала (fallback, если нет фото)."""
        n = (self.category.name if self.category_id else "").lower()
        sp = self.species

        def h(*ks):
            return any(k in n for k in ks)
        if self.unit == "sheet" or "osb" in n:
            fam = "osb"
        elif h("вагонк"):
            fam = "larch" if sp == "larch" else "vagonka"
        elif h("блок"):
            fam = "blokhaus"
        elif h("планкен"):
            fam = "larch" if sp == "larch" else "planken"
        elif h("имитац"):
            fam = "larch" if sp == "larch" else "imitaciya"
        elif h("половая", "террас"):
            fam = "larch" if sp == "larch" else "polovaya"
        elif h("обрезная"):
            fam = "larch_doska" if sp == "larch" else "doska"
        elif h("строганная", "доска"):
            fam = "doska"
        elif h("брус клееный"):
            fam = "brus"
        elif h("рейка", "брусок"):
            fam = "brusok"
        elif h("плинтус", "уголок", "полувалик", "штапик", "раскладка", "наличник"):
            fam = "pogonazh"
        elif h("щит"):
            fam = "shchit"
        elif h("перила", "столб", "балясина", "тетива"):
            fam = "lestnica"
        else:
            fam = "default"
        return "img/products/" + fam + ".jpg"

    @property
    def dimensions(self):
        if self.size_text:
            return self.size_text
        parts = [p for p in (self.thickness, self.width, self.length) if p]
        return " × ".join(str(p) for p in parts)

    @property
    def dimensions_units(self):
        """Размер с единицами: толщина мм × ширина мм × длина м (длина текстом, если диапазон)."""
        parts = []
        if self.thickness:
            parts.append(f"{self.thickness} мм")
        if self.width:
            parts.append(f"{self.width} мм")
        if self.length:
            m = self.length / 1000
            parts.append(("%g" % m).replace(".", ",") + " м")
        else:
            segs = [x.strip() for x in re.split(r'[×хx]', self.size_text or '')]
            if len(segs) >= 3 and segs[-1] and any(ch in segs[-1] for ch in ("м", "–", "-")):
                parts.append(segs[-1])
        if parts:
            return " × ".join(parts)
        return self.size_text

    @property
    def volume_per_piece(self):
        if self.thickness and self.width and self.length:
            return (self.thickness * self.width * self.length) / 1_000_000_000
        return None

    @property
    def price_per_piece(self):
        if self.unit == Unit.M3 and self.volume_per_piece:
            return round(float(self.price) * self.volume_per_piece)
        return None

    @property
    def avg_rating(self):
        approved = self.reviews.filter(is_approved=True)
        if not approved.exists():
            return None
        return round(sum(r.rating for r in approved) / approved.count(), 1)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name="Товар", related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("Фото", upload_to="products/")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Фото товара"
        verbose_name_plural = "Фото товаров"
        ordering = ["order"]

    def __str__(self):
        return f"Фото {self.product_id}"


class Review(models.Model):
    product = models.ForeignKey(Product, verbose_name="Товар", null=True, blank=True,
                                related_name="reviews", on_delete=models.CASCADE)
    author = models.CharField("Имя", max_length=80)
    city = models.CharField("Город", max_length=80, blank=True)
    rating = models.PositiveSmallIntegerField("Оценка", default=5, choices=[(i, str(i)) for i in range(1, 6)])
    text = models.TextField("Текст отзыва")
    is_approved = models.BooleanField("Одобрен (опубликован)", default=False)
    admin_seen = models.BooleanField("Просмотрено администратором", default=False)
    created = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created"]

    def __str__(self):
        target = self.product.name if self.product else "О компании"
        return f"{self.author} - {target}"
