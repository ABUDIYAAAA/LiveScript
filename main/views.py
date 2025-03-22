from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


@login_required
def home(request):
    if not request.user.is_active:
        return render(
            request, "main/home.html", {"message": "Please verify your email to start."}
        )
    return render(request, "main/home.html", {"username": request.user.username})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")
