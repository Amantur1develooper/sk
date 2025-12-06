# projects/templatetags/form_tags.py
from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css):
    """
    Использование в шаблоне:
        {{ form.field|add_class:"form-control" }}
    """
    try:
        widget = field.field.widget
    except AttributeError:
        # на всякий случай, если это не BoundField
        return field

    # уже существующие классы
    existing_classes = widget.attrs.get("class", "")
    if existing_classes:
        new_classes = f"{existing_classes} {css}"
    else:
        new_classes = css

    # объединяем текущие attrs + новые классы
    attrs = {**widget.attrs, "class": new_classes}
    return field.as_widget(attrs=attrs)
