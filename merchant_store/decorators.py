from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

from accounts.permissions import is_customer, is_merchant


def _role_required(check, *, api=False):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if api:
                    return JsonResponse({'error': 'Silakan login terlebih dahulu.'}, status=401)
                return redirect_to_login(request.get_full_path())
            if not check(request.user):
                if api:
                    return JsonResponse({'error': 'Anda tidak memiliki akses.'}, status=403)
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


merchant_required = _role_required(is_merchant)
customer_required = _role_required(is_customer)
customer_required_api = _role_required(is_customer, api=True)
