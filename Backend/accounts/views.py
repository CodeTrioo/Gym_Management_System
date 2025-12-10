from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def register_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data["username"]
        password = data["password"]

        if User.objects.filter(username=username).exists():
            return JsonResponse({"message": "Username already exists"}, status=400)

        User.objects.create_user(username=username, password=password)
        return JsonResponse({"message": "User registered successfully"})
    
    # 👇 ADD THIS so GET request returns something
    return JsonResponse({"message": "Send a POST request only"}, status=400)


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data["username"]
        password = data["password"]

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({"message": "Login successful"})
        return JsonResponse({"message": "Invalid credentials"}, status=400)

    # 👇 ADD THIS so GET request doesn't break the server
    return JsonResponse({"message": "Send a POST request only"}, status=400)

@csrf_exempt
def logout_user(request):
    logout(request)
    return JsonResponse({"message": "Logged out successfully"})
