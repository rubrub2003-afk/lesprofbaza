"""Русские шаблонные фильтры: склонение слов по числу."""
from django import template

register = template.Library()


@register.filter
def plural_ru(n, forms):
    """forms='отзыв,отзыва,отзывов' -> правильная форма для числа n."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return forms.split(",")[-1].strip()
    one, few, many = [f.strip() for f in forms.split(",")]
    nn = abs(n) % 100
    n1 = nn % 10
    if 11 <= nn <= 19:
        return many
    if n1 == 1:
        return one
    if 2 <= n1 <= 4:
        return few
    return many
