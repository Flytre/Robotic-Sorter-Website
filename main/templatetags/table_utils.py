from django import template

register = template.Library()


# template function that's used to get truncated value of an entry in a dictionary
@register.filter
def get_item(dictionary, key):
    if key in dictionary:
        ret = str(dictionary.get(key))
        return ret[:30] + '..' * (len(ret) > 30)
    return 'N/A'


# template math function that calculates column width
@register.filter
def get_width_percent(headers):
    return int((1 / (len(headers) + 1)) * 100)
