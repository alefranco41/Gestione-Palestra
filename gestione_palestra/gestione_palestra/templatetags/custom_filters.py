from django import template

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg


@register.filter
def custom_range(start, end):
    return range(start, end+1)