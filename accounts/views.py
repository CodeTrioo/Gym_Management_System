# CSRF Protection ENABLED
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import json
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'index.html')

@ensure_csrf_cookie
def register_view(request):
    """Render registration page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'register.html')

@require_http_methods(["POST"])
def register_user(request):
    """
    Handle user registration - CSRF PROTECTED     Saves ONLY to auth_user table
    """
    
    print("="*60)
    print("REGISTRATION REQUEST RECEIVED")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"CSRF Token in headers: {'X-CSRFToken' in request.headers}")
    print("="*60)
    
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        # Get form data
        first_name = data.get("firstName") or data.get("first_name", "")
        last_name = data.get("lastName") or data.get("last_name", "")
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        confirm_password = data.get("confirmPassword") or data.get("confirm_password", "")

        print(f"Parsed data:")
        print(f"  First Name: {first_name}")
        print(f"  Last Name: {last_name}")
        print(f"  Email: {email}")

        # Validation
        if not first_name or not last_name:
            print("ERROR: Name missing")
            return JsonResponse({"message": "First name and last name are required"}, status=400)
        
        if not email:
            print("ERROR: Email missing")
            return JsonResponse({"message": "Email is required"}, status=400)
        
        if not password:
            print("ERROR: Password missing")
            return JsonResponse({"message": "Password is required"}, status=400)
        
        if password != confirm_password:
            print("ERROR: Passwords don't match")
            return JsonResponse({"message": "Passwords do not match"}, status=400)
        
        if len(password) < 8:
            print("ERROR: Password too short")
            return JsonResponse({"message": "Password must be at least 8 characters long"}, status=400)
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            print(f"ERROR: Email {email} already exists")
            return JsonResponse({"message": "Email already registered. Please login instead."}, status=400)

        print("Creating user in auth_user table...")
        
        # Create Django User (auth_user)
        django_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        print(f"Created Django User: {django_user.username} (ID: {django_user.id})")
        
        # Log the user in
        login(request, django_user)
        print(f"User logged in via Django auth")

        logger.info(f"User registered successfully: {email}")

        return JsonResponse({
            "message": "Registration successful! Redirecting to dashboard...",
            "redirect": "/dashboard/"
        })
    
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode error: {str(e)}")
        return JsonResponse({"message": "Invalid JSON data"}, status=400)
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({"message": f"Registration failed: {str(e)}"}, status=500)

@ensure_csrf_cookie
def login_view(request):
    """Render login page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'login.html')

@require_http_methods(["POST"])
def login_user(request):
    """
    Handle user login - CSRF PROTECTED     Uses Django's auth_user table
    """
    
    print("="*60)
    print("LOGIN REQUEST RECEIVED")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"CSRF Token in headers: {'X-CSRFToken' in request.headers}")
    print("="*60)
    
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        email = data.get("email") or data.get("username", "").strip().lower()
        password = data.get("password", "")

        print(f"Login attempt for: {email}")

        if not email or not password:
            print("ERROR: Email or password missing")
            return JsonResponse({"message": "Email and password are required"}, status=400)

        # Authenticate using Django's auth system
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            print(f"Authentication successful for: {email}")
            
            # Log the user in
            login(request, user)
            print(f"User logged in via Django auth")
            
            logger.info(f"User logged in successfully: {email}")
            
            return JsonResponse({
                "message": "Login successful",
                "redirect": "/dashboard/"
            })
        else:
            print(f"Authentication failed for: {email}")
            return JsonResponse({"message": "Invalid email or password"}, status=401)
    
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode error: {str(e)}")
        return JsonResponse({"message": "Invalid JSON data"}, status=400)
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        logger.error(f"Login error: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({"message": f"Login failed: {str(e)}"}, status=500)

def logout_user(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('index')

@login_required
def dashboard(request):
    """Dashboard view - SECURED with @login_required"""
    
    context = {
        'user': request.user,
        'user_name': request.user.get_full_name(),
        'user_email': request.user.email,
    }
    
    return render(request, 'dashboard.html', context)
