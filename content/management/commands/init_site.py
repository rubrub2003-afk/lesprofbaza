"""Первичное наполнение боевого сайта: каталог из прайса + демо-данные (если пусто)."""
import os
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
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
        self._ensure_admin()
        self.stdout.write(self.style.SUCCESS("Сайт инициализирован."))

    def _ensure_admin(self):
        """Создаёт администратора из переменных окружения (если заданы)."""
        username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")
        email = os.environ.get("ADMIN_EMAIL", "")
        if not username or not password:
            return
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True})
        user.email = email or user.email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        action = "создан" if created else "обновлён пароль"
        self.stdout.write(self.style.SUCCESS(f"Администратор «{username}» — {action}."))
