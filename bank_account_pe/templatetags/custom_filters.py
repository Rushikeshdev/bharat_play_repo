# myapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def calculate_serial_number(page_number, per_page):
    return (page_number - 1) * per_page 
