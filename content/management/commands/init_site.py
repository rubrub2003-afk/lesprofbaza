"""Первичное наполнение боевого сайта: каталог из прайса + демо-данные (если пусто)."""
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from catalog.models import Product


class Command(BaseCommand):
    help = "Наполнить сайт данными при первом запуске (идемпотентно)"

    def handle(self, *args, **opts):
        if Product.objects.exists():
            self.stdout.write("Каталог уже наполнен — пропускаю.")
        else:
            price = Path(settings.BASE_DIR) / "data" / "price.xlsx"
            if price.exists():
                call_command("import_price", str(price))
            else:
                self.stdout.write(self.style.WARNING("Файл прайса не найден: " + str(price)))
        call_command("seed_demo")
        self.stdout.write(self.style.SUCCESS("Сайт инициализирован."))
