from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from .models import EmailVerificationToken
from django.contrib.auth.decorators import login_required
import re


def index(request):
    return render(request, "landing/login.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = User.objects.filter(username=username).first()

        if user:
            if not user.is_active:
                return render(
                    request,
                    "landing/login.html",
                    {"error": "Your account is not active. Please verify your email."},
                )
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                return render(
                    request,
                    "landing/login.html",
                    {"error": "Invalid username or password. Please try again."},
                )
        else:
            return render(
                request,
                "landing/login.html",
                {"error": "Invalid username or password. Please try again."},
            )
    return render(request, "landing/login.html")


def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        # Check for unique username and email
        username_exists = User.objects.filter(username=username).exists()
        email_exists = User.objects.filter(email=email).exists()

        if username_exists and email_exists:
            return render(
                request,
                "landing/signup.html",
                {
                    "error": "Username and email are already taken. Please choose another username and email."
                },
            )
        elif username_exists:
            return render(
                request,
                "landing/signup.html",
                {"error": "Username is already taken. Please choose another one."},
            )
        elif email_exists:
            return render(
                request,
                "landing/signup.html",
                {"error": "Email is already registered. Please use another email."},
            )

        # Password constraints
        if (
            len(password) < 8
            or not re.search(r"[A-Z]", password)
            or not re.search(r"\d", password)
        ):
            return render(
                request,
                "landing/signup.html",
                {
                    "error": "Password must be at least 8 characters long, contain at least one uppercase letter, and one number."
                },
            )

        if password != confirm_password:
            return render(
                request, "landing/signup.html", {"error": "Passwords do not match."}
            )

        user = User.objects.create_user(
            username=username, email=email, password=password, is_active=False
        )
        token = get_random_string(64)
        EmailVerificationToken.objects.create(user=user, token=token)

        # Send verification email
        verification_link = f"http://127.0.0.1:8000/verify/{token}/"
        email_body = render_to_string(
            "landing/verification_email.html",
            {
                "username": username,
                "verification_link": verification_link,
            },
        )
        send_mail(
            "Verify your LiveScript account",
            "",
            "noreply@livescript.com",
            [email],
            html_message=email_body,
        )
        return redirect("login")  # Redirect to login after signup
    return render(request, "landing/signup.html")


def verify_email(request, token):
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        if verification_token.is_valid():
            user = verification_token.user
            user.is_active = True
            user.save()
            verification_token.delete()
            return render(
                request,
                "landing/login.html",
                {"message": "Your email has been verified. You can now log in."},
            )
        else:
            return render(
                request,
                "landing/login.html",
                {"error": "Verification link has expired."},
            )
    except EmailVerificationToken.DoesNotExist:
        return render(
            request, "landing/login.html", {"error": "Invalid verification link."}
        )
