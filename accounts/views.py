from django.contrib import messages
from copy import copy

from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from .forms import ProfileForm, ProfilePasswordForm, RegistrationForm
from .permissions import is_merchant


class AccountLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'redirect': self.get_success_url()})
        user = form.get_user()
        name = user.first_name or user.get_username()
        messages.success(self.request, f'Selamat datang kembali, {name}!')
        return response

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            return JsonResponse({'ok': False, 'errors': errors}, status=400)
        return super().form_invalid(form)


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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'redirect': reverse_lazy('accounts:login')})
        messages.success(request, 'Akun berhasil dibuat. Silakan login.')
        return redirect('accounts:login')
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
        return JsonResponse({'ok': False, 'errors': errors}, status=400)
    return render(request, 'accounts/register.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    user_profile = getattr(request.user, 'profile', None)
    if user_profile is None:
        return redirect('main:home')

    editing_details = request.method == 'POST' and request.POST.get('action') == 'update_details'
    changing_password = request.method == 'POST' and request.POST.get('action') == 'change_password'
    form = ProfileForm(request.POST if editing_details else None, instance=copy(request.user))
    password_form = ProfilePasswordForm(
        request.user, request.POST if changing_password else None, prefix='password',
    )
    context = {'profile_form': form, 'password_form': password_form}
    if editing_details:
        if form.is_valid():
            form.save()
            messages.success(request, 'Data diri berhasil diperbarui.')
            return redirect('accounts:profile')
        context['open_dialog'] = 'profile-edit-dialog'
        return render(request, 'accounts/profile.html', context)

    if changing_password:
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password berhasil diubah.')
            return redirect('accounts:profile')
        context['open_dialog'] = 'profile-password-dialog'
        return render(request, 'accounts/profile.html', context)

    if request.method == 'POST':
        # Hapus foto profil
        if request.POST.get('action') == 'delete_photo':
            if user_profile.photo:
                user_profile.photo.delete(save=False)  # hapus file dari penyimpanan
                user_profile.photo = None
                user_profile.save(update_fields=['photo'])
                messages.success(request, 'Foto profil berhasil dihapus.')
            else:
                messages.info(request, 'Kamu belum memiliki foto profil.')
            return redirect('accounts:profile')

        photo = request.FILES.get('photo')

        if not photo:
            messages.error(request, 'Pilih foto terlebih dahulu.')
            return redirect('accounts:profile')

        # ukuran unggahan hingga 5 MB.
        if photo.size > 5 * 1024 * 1024:
            messages.error(request, 'Ukuran foto maksimal 5 MB.')
            return redirect('accounts:profile')

        # file gambar.
        if not photo.content_type or not photo.content_type.startswith('image/'):
            messages.error(request, 'File harus berupa gambar.')
            return redirect('accounts:profile')

        user_profile.photo = photo
        user_profile.save(update_fields=['photo'])

        messages.success(request, 'Foto profil berhasil diperbarui.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', context)


@require_http_methods(['GET', 'POST'])
def password_reset_request(request):
    """
    Step 2 & 3: Masukkan email dan username -> Django memvalidasi kecocokan di database.
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()

        if not email or not username:
            err = 'Email dan username wajib diisi.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': err}, status=400)
            return render(request, 'accounts/password_reset.html', {'error': err, 'email': email, 'username': username})

        User = get_user_model()
        # Find user by username
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            err = f'Pengguna dengan username "{username}" tidak ditemukan.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': err}, status=404)
            return render(request, 'accounts/password_reset.html', {'error': err, 'email': email, 'username': username})

        # Validate that email matches user's email
        if user.email and user.email.lower() != email.lower():
            err = f'Email "{email}" tidak cocok dengan akun username "{username}".'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': err}, status=400)
            return render(request, 'accounts/password_reset.html', {'error': err, 'email': email, 'username': username})
        elif not user.email:
            user.email = email
            user.save(update_fields=['email'])

        request.session['reset_user_id'] = user.pk
        display_name = user.first_name or user.username
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'username': user.username, 'display_name': display_name})
        return redirect('accounts:password_reset_confirm')

    return render(request, 'accounts/password_reset.html')


@require_http_methods(['GET', 'POST'])
def password_reset_confirm_direct(request):
    """
    Step 4 & 5: Form password baru -> Django menyimpan password baru menggunakan mekanisme password Django.
    """
    user_id = request.session.get('reset_user_id')
    User = get_user_model()
    user = User.objects.filter(pk=user_id).first() if user_id else None

    if not user:
        err = 'Sesi reset kata sandi telah kedaluwarsa. Silakan ulangi langkah pertama.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': err}, status=400)
        messages.error(request, err)
        return redirect('accounts:password_reset')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        if not password or not password_confirm:
            err = 'Semua kolom kata sandi wajib diisi.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': err}, status=400)
            return render(request, 'accounts/password_reset_confirm.html', {'error': err, 'user_target': user})

        if len(password) < 8:
            err = 'Kata sandi minimal harus 8 karakter.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': err}, status=400)
            return render(request, 'accounts/password_reset_confirm.html', {'error': err, 'user_target': user})

        if password != password_confirm:
            err = 'Kata sandi baru dan konfirmasi kata sandi tidak cocok.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': err}, status=400)
            return render(request, 'accounts/password_reset_confirm.html', {'error': err, 'user_target': user})

        try:
            validate_password(password, user)
        except ValidationError as e:
            err = ' '.join(e.messages)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': err}, status=400)
            return render(request, 'accounts/password_reset_confirm.html', {'error': err, 'user_target': user})

        # Save new password using Django's secure hashing mechanism
        user.set_password(password)
        user.save()
        if 'reset_user_id' in request.session:
            del request.session['reset_user_id']

        msg = 'Kata sandi berhasil diubah! Silakan masuk dengan kata sandi baru.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'message': msg, 'username': user.username})
        messages.success(request, msg)
        return redirect('accounts:login')

    return render(request, 'accounts/password_reset_confirm.html', {'user_target': user})
