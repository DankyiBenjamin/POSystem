from django import template
from accounts.models import Shop

register = template.Library()


@register.simple_tag(takes_context=True)
def get_selected_shop(context):
    request = context['request']
    shop_id = request.session.get('selected_shop_id')
    if shop_id:
        try:
            return Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            return None
    return None
