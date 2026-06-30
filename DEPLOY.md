# Деплой ЛЕСПРОФБАЗА на Render (бесплатно, без карты)

Проект подготовлен: gunicorn, WhiteNoise, PostgreSQL, авто-наполнение каталога и
данных при первом запуске (`init_site`), конфиг `render.yaml`.

## Шаг 1. GitHub
1. Регистрация: https://github.com/signup
2. New repository → имя `lesprofbaza` → Public → Create.
3. «uploading an existing file» → перетащите ВСЁ из папки `site`
   (config, catalog, orders, content, templates, static, data, manage.py,
   requirements.txt, render.yaml, build.sh, Procfile …) → Commit changes.

## Шаг 2. Render
1. https://render.com → Sign up (через GitHub — проще).
2. New → Blueprint → выберите репозиторий `lesprofbaza` → Apply.
3. Render по `render.yaml` сам создаст базу, соберёт статику, применит миграции,
   наполнит каталог (111 товаров) и запустит сайт. Ждать ~5–10 минут.
4. Готово: адрес вида `https://lesprofbaza.onrender.com`.

## Шаг 3. Администратор (один раз)
В Render → ваш web-сервис → вкладка **Shell**:
```
python manage.py createsuperuser
```
Админка: `https://<ваш-адрес>/admin/`

## Позже
- Уведомления: добавьте в Render → Environment переменные
  `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `EMAIL_HOST*`, `ORDER_NOTIFY_EMAIL`.
- Свой домен `lesprofbaza.ru` → Render → Custom Domains + настройка DNS.
