from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect


def logout_view(request):
    logout(request)
    return redirect('/')