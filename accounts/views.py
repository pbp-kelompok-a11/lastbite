from django.contrib.auth.decorators import login_required
from .permissions import is_merchant
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm
from .permissions import is_merchant



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


@login_required
def profile(request):
    # Merchant Membuka profil Merchant
    if not is_merchant(request.user):
        return redirect('main:home')

    user_profile = request.user.profile

    if request.method == 'POST':
        photo = request.FILES.get('photo')

        if not photo:
            messages.error(request, 'Pilih foto terlebih dahulu.')
            return redirect('accounts:profile')

        #ukuran unggahan hingga 5 MB.
        if photo.size > 5 * 1024 * 1024:
            messages.error(request, 'Ukuran foto maksimal 5 MB.')
            return redirect('accounts:profile')

        #file gambar.
        if not photo.content_type or not photo.content_type.startswith('image/'):
            messages.error(request, 'File harus berupa gambar.')
            return redirect('accounts:profile')

        user_profile.photo = photo
        user_profile.save(update_fields=['photo'])

        messages.success(request, 'Foto profil berhasil diperbarui.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html')
