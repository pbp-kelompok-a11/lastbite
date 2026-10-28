from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistrationForm


def auth_modal_forms(request):
    """Provide login and register forms to every template for the auth modal."""
    if request.user.is_authenticated:
        return {}
    return {
        'modal_login_form': AuthenticationForm(),
        'modal_register_form': RegistrationForm(),
    }
