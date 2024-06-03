from django import template

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg


@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def divide(value, arg):
    return value / arg

@register.filter
def custom_range(start, end):
    return range(start, end+1)

@register.filter
def custom_len(iterable):
    return len(iterable)

@register.filter
def star_rating(value):
    full_stars = int(value)
    empty_stars = 5 - full_stars
    return '★' * full_stars + '☆' * empty_stars