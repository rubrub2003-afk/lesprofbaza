"""Импорт каталога из нового многолистового прайса (Сосна/ель + Лиственница).

Запуск:
  python manage.py import_price [путь.xlsx] [--dry]
Полностью пересобирает товары по прайсу (старые товары удаляются).
Вагонка из липы пока пропускается. OSB не импортируется.
"""
import re
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
import openpyxl

UNIT = {'м²': 'm2', 'м³': 'm3', 'пог. м': 'rm', 'пог.м': 'rm', 'шт': 'pc'}
GROUPS = ["Вагонка", "Доска", "Брус и брусок", "Фасадные материалы",
          "Погонаж", "Мебельный щит", "Элементы лестниц", "Плиты"]


def money(s):
    if s is None:
        return None, None
    s = str(s).replace('\xa0', ' ')
    unit = None
    for k, v in UNIT.items():
        if k in s:
            unit = v
            break
    m = re.search(r'(\d[\d\s]*)', s)
    price = int(m.group(1).replace(' ', '')) if m else None
    return price, unit


def parse_dims(text):
    """→ (thickness, width, length_mm, size_text). Чистый разбор только для 'A × B × C'."""
    st = str(text).strip()
    parts = re.split(r'[×хx]', st)
    nums = []
    for p in parts:
        m = re.search(r'\d+(?:[.,]\d+)?', p)
        nums.append(float(m.group(0).replace(',', '.')) if m else None)
    t = w = l = None
    clean = [n for n in nums if n is not None]
    if len(parts) >= 3 and nums[0] and nums[1] and nums[2] is not None:
        t, w, lm = nums[0], nums[1], nums[2]
        l = lm * 1000 if lm <= 20 else lm            # 3-е число ≤20 → метры
    elif len(parts) == 2 and nums[0] and nums[1] is not None:
        w, lm = nums[0], nums[1]
        l = lm * 1000 if lm <= 20 else lm
    return (int(t) if t else None, int(w) if w else None,
            int(l) if l else None, st)


# базовое имя по секции/подгруппе + категория (группа) + стандарт
def soft_meta(section, subgroup):
    sub = (subgroup or "").lower()
    S = section
    if S == "БРУСОК":
        base = "Рейка" if "рейка" in sub else "Брусок"
        grade = "2 сорт" if "сорт 2" in sub else ""
        return base, "Брус и брусок", "", grade
    if S == "ПЛИНТУС":
        return ("Европлинтус" if "европлинтус" in sub else "Плинтус"), "Погонаж", "", ""
    if S == "УГОЛОК":
        return "Уголок", "Погонаж", "", ""
    if S == "ПОЛУВАЛИК":
        return ("Штапик" if "штапик" in sub else "Полувалик"), "Погонаж", "", ""
    if S == "РАСКЛАДКА":
        return "Раскладка", "Погонаж", "", ""
    if S == "НАЛИЧНИК":
        return "Наличник", "Погонаж", "", ""
    if S == "МЕБЕЛЬНЫЙ ЩИТ":
        if "клееный брус" in sub:
            return "Брус клееный", "Брус и брусок", "", ""
        if "тетива" in sub:
            return "Тетива", "Элементы лестниц", "", ""
        if "перила" in sub:
            return "Перила", "Элементы лестниц", "", ""
        if "столб" in sub:
            return "Столб", "Элементы лестниц", "", ""
        if "балясина" in sub:
            return "Балясина", "Элементы лестниц", "", ""
        return "Мебельный щит", "Мебельный щит", "", ""
    if S == "ВАГОНКА ШТИЛЬ":
        return ("Евровагонка" if "евровагонка" in sub else "Вагонка штиль"), "Вагонка", "", ""
    if S == "ИМИТАЦИЯ БРУСА":
        return "Имитация бруса", "Фасадные материалы", "", ""
    if S == "ПОЛОВАЯ ДОСКА":
        return "Половая доска", "Доска", "", ""
    if S == "ДОСКА СТРОГАННАЯ":
        return "Доска строганная", "Доска", "", ""
    if S == "БЛОК-ХАУС":
        return "Блок-хаус", "Фасадные материалы", "", ""
    if S == "ПЛАНКЕН":
        return ("Планкен косой" if "косой" in sub else "Планкен"), "Фасадные материалы", "", ""
    if S and S.startswith("ДОСКА ОБРЕЗНАЯ"):
        std = ""
        if "камерн" in sub: std = "камерная сушка"
        elif "гост" in sub: std = "ГОСТ"
        elif "ту" in sub: std = "ТУ"
        grade = "2 сорт" if "второй сорт" in sub else ""
        return "Доска обрезная", "Доска", std, grade
    return None


def parse_softwood(ws):
    sec_re = re.compile(r'^\s*\d+\.\s+([А-ЯЁ].*)')
    section = subgroup = None
    cur_price = cur_unit = None
    out = []
    for r in ws.iter_rows(values_only=True):
        F = str(r[5]).strip() if r[5] is not None else ''
        G = str(r[6]).strip() if r[6] is not None else ''
        J = r[9]
        if not F and not G:
            continue
        m = sec_re.match(F)
        if m:
            section = m.group(1).strip(); subgroup = None
            cur_price = cur_unit = None
            continue
        if F and not re.match(r'^\d+$', F):
            pr, un = money(F)
            if pr and '₽' in F:
                cur_price, cur_unit = pr, un
            subgroup = F
            continue
        if re.match(r'^\d+$', F) and G:
            pr, un = money(J)
            if pr:
                cur_price, cur_unit = pr, un
            meta = soft_meta(section, subgroup)
            if not meta or section == "ВАГОНКА (Липа)":
                continue
            base, group, std, grade = meta
            out.append(dict(base=base, group=group, standard=std, grade=grade,
                            size=G, price=cur_price, unit=cur_unit,
                            species="pine_spruce"))
    return out


LARCH_MATRIX = {
    "вагонка из лиственницы": ("Вагонка лиственница", "Вагонка", "larch"),
    "террасная": ("Террасная доска лиственница", "Фасадные материалы", "larch"),
    "половая доска из лиственницы": ("Половая доска лиственница", "Доска", "larch"),
    "планкен лиственница": ("Планкен лиственница", "Фасадные материалы", "larch"),
    "имитация бруса лиственница": ("Имитация бруса лиственница", "Фасадные материалы", "larch"),
    "вагонка из ангарской сосны": ("Вагонка ангарская сосна", "Вагонка", "pine_spruce"),
}


def parse_larch(ws):
    rows = list(ws.iter_rows(values_only=True))
    out = []
    cur = None          # (base, group, species) for matrix sections
    mode = None         # 'matrix' | 'shchit' | 'obrezn'
    cur_price = None
    for r in rows:
        cells = [(str(c).strip() if c is not None else '') for c in r]
        C, D, E, Fc, G, H, I = (cells[2], cells[3], cells[4], cells[5],
                                cells[6], cells[7], cells[8])
        joined = " ".join(cells).lower()
        # section switch
        matched = False
        for key, val in LARCH_MATRIX.items():
            if key in C.lower():
                cur = val; mode = 'matrix'; matched = True; break
        if matched:
            continue
        if "мебельный щит из лиственницы" in C.lower():
            mode = 'shchit'; continue
        if "обрезная доска из лиственницы" in C.lower():
            mode = 'obrezn'; cur_price = None; continue
        # skip header rows
        if C in ("Толщина, мм", "Длина", "") and not re.match(r'^\d', C):
            continue
        # data rows
        if mode == 'matrix' and re.match(r'^\d', C) and D:
            base, group, species = cur
            th = int(re.search(r'\d+', C).group())
            wm = re.search(r'\d+', D)
            wd = int(wm.group()) if wm else None
            sorts = {'Экстра': E, 'Прима': Fc, 'АВ/В': G, 'ВС/С': H, 'СД/Д': I}
            def num(x):
                m = re.search(r'\d[\d\s]*', str(x))
                return int(m.group().replace(' ', '')) if m else None
            price = num(Fc) or num(E) or num(G)      # Прима, иначе Экстра/АВ
            if not price:
                continue
            size = (f"{th} × {wd}" if wd else f"{th}") + " × 2–4 м"
            rows = "".join(f"<tr><td>{k}</td><td>{num(v):,} ₽</td></tr>".replace(",", " ")
                           for k, v in sorts.items() if num(v))
            desc = ('<p class="sortnote">Цена зависит от сорта древесины (за м²):</p>'
                    '<table class="sorts"><tr><th>Сорт</th><th>Цена</th></tr>' + rows + '</table>')
            out.append(dict(base=base, group=group, standard="", grade="Прима",
                            size=size, price=price, unit="m2", species=species,
                            thickness=th, width=wd, length=None, desc=desc))
        elif mode == 'obrezn' and re.match(r'^\d', C) and D:
            pr, un = money(Fc)
            if pr:
                cur_price = pr
            th = int(re.search(r'\d+', C).group())
            wd = int(re.search(r'\d+', D).group())
            ln = re.search(r'\d+', E)
            lnmm = int(ln.group()) * 1000 if ln else None
            out.append(dict(base="Доска обрезная лиственница", group="Доска",
                            standard="", grade="", size=f"{th} × {wd} × {E}",
                            price=cur_price, unit="m3", species="larch",
                            thickness=th, width=wd, length=lnmm, desc=""))
        elif mode == 'shchit' and re.match(r'^\d', C):
            th = int(re.search(r'\d+', C).group())
            pr = re.search(r'\d[\d\s]*', str(G))
            price = int(pr.group().replace(' ', '')) if pr else None
            if not price:
                continue
            out.append(dict(base="Мебельный щит лиственница", group="Мебельный щит",
                            standard="", grade=(Fc or ""), size=f"{th} × {D} × 2–4 м",
                            price=price, unit="m2", species="larch",
                            thickness=th, width=None, length=None, desc=""))
    return out


def parse_osb(ws):
    out = []
    for r in ws.iter_rows(values_only=True):
        cells = [(str(c).strip() if c is not None else '') for c in r]
        A, B, C = cells[0], cells[1], cells[2]
        if re.match(r'^\d+$', A) and B and C:
            th = int(A)
            m = re.search(r'\d[\d\s]*', C)
            price = int(m.group().replace(' ', '')) if m else None
            if not price:
                continue
            sheet = B.replace('x', '×').replace('X', '×').replace('х', '×').strip()
            out.append(dict(base="OSB-плита", group="Плиты", standard="", grade="",
                            size=f"{th} мм", size_text=f"лист {sheet} м",
                            price=price, unit="sheet", species="other",
                            thickness=th, width=None, length=None,
                            desc=("Ориентированно-стружечная плита OSB-3 — прочная и влагостойкая. "
                                  "Для чернового пола, обшивки стен, кровли и опалубки. "
                                  f"Размер листа {sheet} м, толщина {th} мм.")))
    return out


class Command(BaseCommand):
    help = "Импорт каталога из нового прайса"

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="?", default=None)
        parser.add_argument("--dry", action="store_true")

    def handle(self, *args, **opts):
        path = opts["path"] or str(Path(settings.BASE_DIR) / "data" / "price.xlsx")
        wb = openpyxl.load_workbook(path, data_only=True)
        soft = parse_softwood(wb["Сосна и ель"])
        larch = parse_larch(wb["Лиственница"])
        osb = parse_osb(wb["Sheet3"]) if "Sheet3" in wb.sheetnames else []
        items = soft + larch + osb
        # финальные поля
        for it in items:
            if "thickness" not in it:
                t, w, l, stext = parse_dims(it["size"])
                it["thickness"], it["width"], it["length"] = t, w, l
            it["size_text"] = it.get("size_text") or it["size"]
            name = f"{it['base']} {it['size']}"
            if it.get("standard"):
                name += f", {it['standard']}"
            it["name"] = name

        from collections import Counter
        by_group = Counter(it["group"] for it in items)
        by_species = Counter(it["species"] for it in items)
        self.stdout.write(f"Всего товаров: {len(items)}")
        for g in GROUPS:
            self.stdout.write(f"  {by_group.get(g,0):3d}  {g}")
        self.stdout.write(f"Породы: {dict(by_species)}")
        no_price = [it for it in items if not it["price"]]
        self.stdout.write(f"Без цены: {len(no_price)}")

        if opts["dry"]:
            self.stdout.write("\n--- ЛИСТВЕННИЦА (образцы) ---")
            for it in larch[:6] + larch[-4:]:
                self.stdout.write(f"  {it['name']} | {it['price']} {it['unit']} | {it['species']}")
            return

        from catalog.models import Category, Product
        with transaction.atomic():
            # группы
            groups = {}
            for i, g in enumerate(GROUPS):
                obj, _ = Category.objects.get_or_create(name=g, parent=None,
                                                        defaults={"order": i})
                groups[g] = obj
            # чистим старые товары и подкатегории
            Product.objects.all().delete()
            Category.objects.filter(parent__isnull=False).delete()
            # подкатегории (по базовому имени в своей группе)
            subcats = {}
            def subcat(base, group):
                key = (base, group)
                if key not in subcats:
                    subcats[key], _ = Category.objects.get_or_create(
                        name=base, parent=groups[group])
                return subcats[key]
            created = 0
            for it in items:
                if not it["price"]:
                    continue
                cat = subcat(it["base"], it["group"])
                Product.objects.create(
                    category=cat, name=it["name"], species=it["species"],
                    grade=it.get("grade", ""), standard=it.get("standard", ""),
                    thickness=it.get("thickness"), width=it.get("width"),
                    length=it.get("length"), size_text=it["size_text"],
                    unit=it["unit"], price=it["price"],
                    description=it.get("desc", ""), in_stock=True, is_active=True)
                created += 1
            self.stdout.write(self.style.SUCCESS(f"Создано товаров: {created}, подкатегорий: {len(subcats)}"))
