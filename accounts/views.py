from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm


class AccountLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Selamat datang kembali, {form.get_user().get_username()}!')
        return response


@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('main:home')
    role = request.GET.get('role', 'customer')
    if role not in ('customer', 'merchant'):
        role = 'customer'
    form = RegistrationForm(request.POST if request.method == 'POST' else None, initial={'role': role})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Akun berhasil dibuat. Silakan login.')
        return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'form': form})
