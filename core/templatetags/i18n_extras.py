from django import template

register = template.Library()


@register.filter
def localized(obj, field):
    if obj is None:
        return ""
    getter = getattr(obj, "get_translated", None)
    if callable(getter):
        return getter(field)
    return getattr(obj, field, "") or ""


@register.filter
def localized_default(obj, fields):
    if obj is None:
        return ""
    getter = getattr(obj, "get_translated", None)
    field_names = fields.split(",")
    if callable(getter):
        values = [getter(field.strip()) for field in field_names]
        return next((value for value in values if value), values[0] if values else "")
    return next((getattr(obj, field.strip(), "") for field in field_names if getattr(obj, field.strip(), "")), "")


@register.filter
def has_lang(obj, code):
    if obj is None:
        return False
    return code in obj.translated_languages()
