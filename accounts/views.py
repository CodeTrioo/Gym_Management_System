from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from accounts.models import UserProfile
from staff_control.models import StaffPermission
import json
import logging

logger = logging.getLogger(__name__)
signer = TimestampSigner()


def index(request):
    return redirect('overview')


@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    return render(request, 'accounts/register.html')


@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        email = data.get("email", "").strip().lower()
        full_name = data.get("full_name", "").strip()
        password = data.get("password", "")
        confirm_password = data.get("confirmPassword") or data.get("confirm_password", "")

        if not email:
            return JsonResponse({"message": "Email is required"}, status=400)
        if not password:
            return JsonResponse({"message": "Password is required"}, status=400)
        if password != confirm_password:
            return JsonResponse({"message": "Passwords do not match"}, status=400)
        if len(password) < 8:
            return JsonResponse({"message": "Password must be at least 8 characters"}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({"message": "Email already registered. Please login."}, status=400)

        registration_data = {
            'email': email,
            'full_name': full_name,
            'password': password
        }
        token = signer.sign_object(registration_data)
        activation_url = request.build_absolute_uri(reverse('activate_account', args=[token]))
        
        email_body = render_to_string('accounts/activation_email.txt', {'activation_url': activation_url})
        send_mail(
            'Verify your GymPro Account',
            email_body,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return JsonResponse({"message": "Please check your email to complete registration. The link expires in 24 hours.", "redirect": ""})

    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return JsonResponse({"message": f"Registration failed: {str(e)}"}, status=500)


def activate_account(request, token):
    try:
        data = signer.unsign_object(token, max_age=86400) # 24 hours
    except SignatureExpired:
        return render(request, 'accounts/activation_invalid.html', {'message': 'The activation link has expired. Please register again.'})
    except BadSignature:
        return render(request, 'accounts/activation_invalid.html', {'message': 'The activation link is invalid.'})

    email = data.get('email')
    full_name = data.get('full_name')
    password = data.get('password')

    if User.objects.filter(email=email).exists():
        return redirect('login')

    user = User.objects.create_user(username=email, email=email, password=password)
    if full_name:
        names = full_name.split(' ', 1)
        user.first_name = names[0]
        if len(names) > 1:
            user.last_name = names[1]
        user.save()

    profile = UserProfile.objects.create(user=user, role='member')
    
    return render(request, 'accounts/activation_success.html')


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    return render(request, 'accounts/login.html')


@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        # Resolve the actual username for authentication – allows login with email even if username differs
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        try:
            user_obj = UserModel.objects.get(email=email)
            auth_username = user_obj.username
        except UserModel.DoesNotExist:
            auth_username = email

        if not email or not password:
            return JsonResponse({"message": "Email and password are required"}, status=400)

        user = authenticate(request, username=auth_username, password=password)
        if user is not None:
            login(request, user)
            redirect_url = _get_portal_url(user)
            return JsonResponse({"message": "Login successful", "redirect": redirect_url})
        else:
            return JsonResponse({"message": "Invalid email or password"}, status=401)

    except Exception as e:
        return JsonResponse({"message": f"Login failed: {str(e)}"}, status=500)


def logout_user(request):
    logout(request)
    return redirect('login')


def _redirect_by_role(user):
    return redirect(_get_portal_url(user))


def _get_portal_url(user):
    if getattr(user, 'is_superuser', False):
        return '/portal/admin/'
    try:
        role = user.profile.role
        if role == 'admin':
            return '/portal/admin/'
        elif role == 'staff':
            return '/portal/staff/'
    except Exception:
        pass
    return '/portal/member/'


# Admin: Create Staff Account
@login_required
def create_staff(request):
    try:
        if request.user.profile.role != 'admin':
            return JsonResponse({"message": "Unauthorized"}, status=403)
    except Exception:
        return JsonResponse({"message": "Unauthorized"}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            email = data.get('email', '').strip().lower()
            full_name = data.get('full_name', '').strip()
            password = data.get('password', '')
            speciality = data.get('speciality', '')

            if not email or not password:
                return JsonResponse({"message": "Email and password required"}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({"message": "Email already exists"}, status=400)

            user = User.objects.create_user(username=email, email=email, password=password)
            if full_name:
                names = full_name.split(' ', 1)
                user.first_name = names[0]
                if len(names) > 1:
                    user.last_name = names[1]
                user.save()

            profile = UserProfile.objects.create(user=user, role='staff', speciality=speciality)
            StaffPermission.get_or_create_for_staff(user)

            return JsonResponse({"message": "Staff account created!", "staff_id": user.id})
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)

    return JsonResponse({"message": "Method not allowed"}, status=405)


# Admin: Update staff profile
@login_required
def update_staff_profile(request, staff_id):
    try:
        if request.user.profile.role != 'admin':
            return JsonResponse({"message": "Unauthorized"}, status=403)
    except Exception:
        return JsonResponse({"message": "Unauthorized"}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            staff_user = get_object_or_404(User, id=staff_id)
            
            full_name = data.get('full_name', '').strip()
            if full_name:
                names = full_name.split(' ', 1)
                staff_user.first_name = names[0]
                staff_user.last_name = names[1] if len(names) > 1 else ''
                staff_user.save()

            profile = staff_user.profile
            profile.speciality = data.get('speciality', profile.speciality)
            profile.bio = data.get('bio', profile.bio)
            profile.phone = data.get('phone', profile.phone)
            profile.address = data.get('address', profile.address)
            profile.profile_image_url = data.get('profile_image_url', profile.profile_image_url)
            profile.save()
            return JsonResponse({"message": "Staff profile updated!"})
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)

    return JsonResponse({"message": "Method not allowed"}, status=405)


@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            profile = request.user.profile
            profile.phone = data.get('phone', profile.phone)
            profile.address = data.get('address', profile.address)
            profile.bio = data.get('bio', profile.bio)
            profile.profile_image_url = data.get('profile_image_url', profile.profile_image_url)
            
            target_weight_kg_val = data.get('target_weight_kg')
            if target_weight_kg_val is not None:
                if target_weight_kg_val == '':
                    profile.target_weight_kg = None
                else:
                    try:
                        profile.target_weight_kg = float(target_weight_kg_val)
                    except ValueError:
                        pass
            
            # Speciality is ONLY updatable by admin (via update_staff_profile)
            # or if the current user is an admin updating their own profile (optional, but keep it safe)
            if profile.role == 'staff' and request.user.profile.role == 'admin':
                profile.speciality = data.get('speciality', profile.speciality)
            
            profile.save()
            return JsonResponse({"message": "Profile updated successfully!"})
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    return JsonResponse({"message": "Method not allowed"}, status=405)
