def is_admin(user):
    return user.is_authenticated and (user.role or '').lower() == 'admin'


def is_manager(user):
    return user.is_authenticated and (user.role or '').lower() == 'manager'


def is_staff(user):
    return user.is_authenticated and (user.role or '').lower() == 'staff'


def is_admin_or_manager(user):
    return user.is_authenticated and (user.role or '').lower() in ['admin', 'manager']


def get_user_shop_queryset(queryset, request):
    user = request.user
    if (user.role or '').lower() != 'admin':
        return queryset.filter(shop=user.shop)

    shop_id = request.GET.get('shop')
    if shop_id:
        return queryset.filter(shop_id=shop_id)

    return queryset
