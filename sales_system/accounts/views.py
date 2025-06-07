from django.contrib.auth.views import LoginView
from .forms import LoginForm, UserCreationForm
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect
from django.contrib import messages


class CustomLoginView(LoginView):
    # Custom login view to use a specific form and template
    authentication_form = LoginForm
    template_name = 'registration/login.html'

# Utitlity function to check if the user is an admin


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


@login_required
# decorator to ensure only admin users can access this view
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully!")
            return redirect('create_user')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/create_user.html', {'form': form})


# for testing purposes
"""
Admin Ben password 1234
manager Yaw Passoword 1234
staff Ama Password 1234
"""
