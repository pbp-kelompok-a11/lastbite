from .models import UserProfile


def has_role(user, role):
    if not user.is_authenticated:
        return False
    try:
        return user.profile.role == role
    except UserProfile.DoesNotExist:
        return False


def is_customer(user):
    return has_role(user, UserProfile.Role.CUSTOMER)


def is_merchant(user):
    return has_role(user, UserProfile.Role.MERCHANT)
