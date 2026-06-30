"""
Импорт прайс-листа ЛЕСПРОФБАЗА из Excel в каталог.

Раскладывает 15 секций прайса по 7 разделам сайта, переносит цену на группы
размеров (как в исходном файле), парсит размеры и единицы измерения.

Запуск:
    python manage.py import_price "путь/к/Прайс-лист.xlsx"
    python manage.py import_price ... --keep   # не очищать каталог перед импортом
"""
import re
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from catalog.models import Category, Product

# секция → (группа, подкатегория, порода, стандарт, префикс названия)
SECTION_MAP = {
    1:  ("Вагонка", "Вагонка липа", "linden", "", "Вагонка липа"),
    2:  ("Брус и брусок", "Брусок и рейка", "pine_spruce", "", "Брусок"),
    3:  ("Погонаж", "Плинтус", "pine_spruce", "", "Плинтус"),
    4:  ("Погонаж", "Уголок", "pine_spruce", "", "Уголок"),
    5:  ("Погонаж", "Полувалик и штапик", "pine_spruce", "", "Полувалик/штапик"),
    6:  ("Погонаж", "Раскладка", "pine_spruce", "", "Раскладка"),
    7:  ("Погонаж", "Наличник", "pine_spruce", "", "Наличник"),
    10: ("Фасадные материалы", "Имитация бруса", "pine_spruce", "", "Имитация бруса"),
    11: ("Доска", "Половая доска", "pine_spruce", "", "Половая доска"),
    12: ("Доска", "Доска строганная", "pine_spruce", "", "Доска строганная"),
    13: ("Фасадные материалы", "Блок-хаус", "pine_spruce", "", "Блок-хаус"),
    14: ("Фасадные материалы", "Планкен", "pine_spruce", "", "Планкен прямой"),
}
SUB8 = {
    "сучковые":      ("Мебельный щит", "Мебельный щит", "Мебельный щит"),
    "клееный брус":  ("Брус и брусок", "Брус клееный", "Брус клееный"),
    "перила":        ("Элементы лестниц", "Перила", "Перила"),
    "столб":         ("Элементы лестниц", "Столбы", "Столб"),
    "балясина":      ("Элементы лестниц", "Балясины", "Балясина"),
}
GROUP_ORDER = ["Вагонка", "Доска", "Брус и брусок", "Фасадные материалы",
               "Погонаж", "Мебельный щит", "Элементы лестниц"]


def parse_price(text):
    """'250 (300) ₽ / шт.' → (Decimal('250'), 'pc'). Берём базовое значение до скобки."""
    if not text or "₽" not in str(text):
        return None, None
    head = str(text).split("₽")[0]
    head = head.split("(")[0]
    digits = re.sub(r"[^\d]", "", head)
    if not digits:
        return None, None
    price = Decimal(digits)
    low = str(text).lower()
    if "м²" in low or "м2" in low:
        unit = "m2"
    elif "м³" in low or "м3" in low:
        unit = "m3"
    elif "пог" in low:
        unit = "rm"
    else:
        unit = "pc"
    return price, unit


def parse_dims(size):
    """'25 × 100 × 6' → (25, 100, 6000). Третье число — длина в метрах, переводим в мм.
    Возвращает (t, w, l_mm) или (None, None, None), если размер нестандартный."""
    m = re.match(r"^\s*(\d+)\s*[×x]\s*(\d+)\s*[×x]\s*([\d.]+)\s*$", str(size))
    if not m:
        return None, None, None
    t, w, c = int(m.group(1)), int(m.group(2)), float(m.group(3))
    if c <= 12:                      # это длина в метрах
        return t, w, int(round(c * 1000))
    return None, None, None          # неоднозначно (напр. балясина 50×50×90) — пропускаем


def resolve(section, subgroup):
    sg = (subgroup or "").lower()
    if section == 8:
        for key, (g, sc, pref) in SUB8.items():
            if key in sg:
                return (g, sc, "pine_spruce", "", pref)
        return None
    if section == 9:
        if "евровагон" in sg:
            return ("Вагонка", "Евровагонка", "pine_spruce", "", "Евровагонка")
        return ("Вагонка", "Вагонка штиль", "pine_spruce", "", "Вагонка штиль")
    if section == 14:
        if "косой" in sg:
            return ("Фасадные материалы", "Планкен", "pine_spruce", "", "Планкен косой")
        return SECTION_MAP[14]
    if section == 15:
        std = "ГОСТ" if "гост" in sg else ("ТУ" if sg.startswith("ту") else "")
        return ("Доска", "Доска обрезная", "pine_spruce", std, "Доска обрезная")
    if section == 3 and "европлинтус" in sg:
        return ("Погонаж", "Плинтус", "pine_spruce", "", "Европлинтус")
    return SECTION_MAP.get(section)


class Command(BaseCommand):
    help = "Импорт прайс-листа из Excel в каталог"

    def add_arguments(self, parser):
        parser.add_argument("path", help="Путь к .xlsx прайсу")
        parser.add_argument("--keep", action="store_true", help="Не очищать каталог перед импортом")

    def handle(self, *args, **opts):
        try:
            import openpyxl
        except ImportError:
            raise CommandError("Нужен openpyxl: pip install openpyxl")

        wb = openpyxl.load_workbook(opts["path"], data_only=True)
        ws = wb.active

        if not opts["keep"]:
            Product.objects.all().delete()
            Category.objects.all().delete()

        # создаём группы в нужном порядке
        groups = {}
        for i, gname in enumerate(GROUP_ORDER):
            groups[gname] = Category.objects.create(name=gname, order=i)
        subcats = {}

        def get_subcat(group_name, sub_name):
            key = (group_name, sub_name)
            if key not in subcats:
                grp = groups[group_name]
                subcats[key] = Category.objects.create(
                    name=sub_name, parent=grp, order=len(subcats))
            return subcats[key]

        section = None
        subgroup = None
        carry_price = None
        carry_unit = None
        created = 0

        for row in ws.iter_rows(min_row=1, values_only=True):
            f = row[5] if len(row) > 5 else None   # № или заголовок
            size = row[6] if len(row) > 6 else None
            price_cell = row[9] if len(row) > 9 else None

            if isinstance(f, str):
                txt = f.strip()
                msec = re.match(r"^(\d+)\.\s*(.+)$", txt)
                if msec:
                    section = int(msec.group(1))
                    subgroup = None
                else:
                    subgroup = txt          # подгруппа или примечание
                carry_price = None          # цена не «перетекает» через заголовок
                carry_unit = None
                continue

            if isinstance(f, int) and size:
                target = resolve(section, subgroup)
                if not target:
                    continue
                group_name, sub_name, species, standard, prefix = target

                price, unit = parse_price(price_cell)
                if price is not None:
                    carry_price, carry_unit = price, unit
                if carry_price is None:
                    continue                # нет цены — пропускаем

                size_text = str(size).strip()
                t, w, l = parse_dims(size_text)
                name = f"{prefix} {size_text}"
                if standard:
                    name += f", {standard}"

                subcat = get_subcat(group_name, sub_name)
                Product.objects.create(
                    category=subcat, name=name, sku=str(f),
                    species=species, standard=standard,
                    thickness=t, width=w, length=l, size_text=size_text,
                    unit=carry_unit, price=carry_price, in_stock=True,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Импортировано товаров: {created}; групп: {len(groups)}; подкатегорий: {len(subcats)}"))
