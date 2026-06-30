from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Count, Q

from .models import UserProfile
from .forms import (
    LoginForm, RegisterForm,
    UserEditForm, AdminUserEditForm, ProfileEditForm, CustomPasswordChangeForm,
)
from tasks.models import Task


def login_view(request):
    if request.user.is_authenticated:
        return redirect('task_list')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get('next') or 'task_list')
    else:
        form = LoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('task_list')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('task_list')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    assigned_tasks = Task.objects.filter(assigned_to=request.user)
    created_tasks = Task.objects.filter(created_by=request.user)
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'assigned_tasks': assigned_tasks,
        'created_tasks': created_tasks,
    })


@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user = request.user
    is_admin = user.is_superuser or profile.is_admin

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = ProfileEditForm(request.POST, instance=profile)
        if not is_admin:
            profile_form.fields.pop('role', None)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(instance=profile)
        if not is_admin:
            profile_form.fields.pop('role', None)

    return render(request, 'accounts/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})


@login_required
def user_list(request):
    users = User.objects.select_related('profile').annotate(
        task_count=Count('assigned_tasks', filter=Q(assigned_tasks__status__in=['todo', 'in_progress']))
    ).order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_detail(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    assigned_tasks = Task.objects.filter(assigned_to=target_user).order_by('-created_at')
    stats = {
        'total': assigned_tasks.count(),
        'todo': assigned_tasks.filter(status='todo').count(),
        'in_progress': assigned_tasks.filter(status='in_progress').count(),
        'done': assigned_tasks.filter(status='done').count(),
    }
    viewer = request.user
    viewer_profile, _ = UserProfile.objects.get_or_create(user=viewer)
    is_admin = viewer.is_superuser or viewer_profile.is_admin
    return render(request, 'accounts/user_detail.html', {
        'target_user': target_user,
        'profile': profile,
        'assigned_tasks': assigned_tasks,
        'stats': stats,
        'is_admin': is_admin,
        'is_own': viewer.pk == target_user.pk,
    })


@login_required
def user_edit(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    viewer = request.user
    viewer_profile, _ = UserProfile.objects.get_or_create(user=viewer)
    is_admin = viewer.is_superuser or viewer_profile.is_admin

    if not is_admin and viewer.pk != target_user.pk:
        return HttpResponseForbidden("You don't have permission to edit this user.")

    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        user_form = AdminUserEditForm(request.POST, instance=target_user) if is_admin else UserEditForm(request.POST, instance=target_user)
        profile_form = ProfileEditForm(request.POST, instance=profile)
        if not is_admin:
            profile_form.fields.pop('role', None)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f'User "{target_user.username}" updated.')
            return redirect('user_detail', pk=target_user.pk)
    else:
        user_form = AdminUserEditForm(instance=target_user) if is_admin else UserEditForm(instance=target_user)
        profile_form = ProfileEditForm(instance=profile)
        if not is_admin:
            profile_form.fields.pop('role', None)

    return render(request, 'accounts/user_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'target_user': target_user,
        'is_admin': is_admin,
    })


@login_required
def user_delete(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    viewer = request.user
    viewer_profile, _ = UserProfile.objects.get_or_create(user=viewer)

    if not (viewer.is_superuser or viewer_profile.is_admin):
        return HttpResponseForbidden("Only admins can delete users.")

    if target_user.pk == viewer.pk:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f'User "{username}" deleted.')
        return redirect('user_list')

    return render(request, 'accounts/user_confirm_delete.html', {'target_user': target_user})
