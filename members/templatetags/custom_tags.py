from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def can_view_marker(user):

    if not hasattr(user, 'profile'):
        return False

    return user.profile.role in [
        'pastor',
        'administrator',
        'elder',
        'overseer',
    ]